#!/usr/bin/env python3
# Python Network Programming Cookbook -- Chapter - 2
# This program is optimized for Python 2.7 but has been updated for Python 3.
import socket
import sys
import signal
import pickle
import struct
import argparse
import threading
from websockets.sync.client import connect
# Bu, Chat Server'ın WebSocket üzerinden Monitoring Server'a bağlanabilmesini sağlayacak.
import time
import logging # Bu kütüphane, sunucuda gerçekleşen olayları dosyaya kaydetmemizi sağlayacak.
from datetime import datetime


CHAT_SERVER_NAME = 'server'

# Some utilities
# send(): Does not guarantee that all data is sent

# sendall(): A method provided by Python for sending data over a socket
def send(channel, *args):
    # send: The name of the function I defined.
    buffer = pickle.dumps(args)
    value = socket.htonl(len(buffer))
    size = struct.pack("L", value)
    channel.sendall(size)
    channel.sendall(buffer) # sendall() continues sending until all the data has been sent to the other side.

# recv() is a socket function in Python. It is used to read data received from the other side
def receive(channel):
    size_data = b"" # An empty byte sequence where we will store the received data

    while len(size_data) < struct.calcsize("L"):
        part = channel.recv(struct.calcsize("L") - len(size_data))

        if not part:
            return ''

        size_data += part
    try:
        size = socket.ntohl(struct.unpack("L", size_data)[0])
    except struct.error as e:
        return ''
    buf = b""
    while len(buf) < size:
        received_part = channel.recv(size - len(buf))

        if not received_part:
            return ''

        buf += received_part
    return pickle.loads(buf)[0]

class ChatServer:
    """An example chat server using threding."""
    # The IP address and chat port can be configured.
    def __init__(self, port, host, backlog=5):
        self.clients = 0
        self.clientmap = {}
        # This list will only contain the nicknames of users who are currently logged in.
        self.usernames = []

        # Her kullanıcının mesaj gönderme zamanlarını tutacak
        self.message_times = {}

        # Neden sözlük (dict)?
        #
        # Çünkü her kullanıcının mesaj zamanlarını kendi nickname'iyle eşleştireceğiz.

        self.muted_until = {} # for each user's mute end time


        #self.lock, birden fazla thread'in nickname listesini aynı anda değiştirmesini önleyecek.
        self.lock = threading.Lock()
        self.monitor_socket = connect("ws://localhost:8765") # Chat Server ile Monitoring Server arasında WebSocket bağlantısı kuruyor
        self.monitor_lock = threading.Lock() # WebSocket bağlantısına aynı anda birden fazla thread'in mesaj göndermesini engellemek için kullanılır.

        self.outputs = []  # list of output sockets

        # To configure logging settings
        logging.basicConfig(
            filename='chat_server.txt', # filename: The file where the records will be stored.
            level=logging.INFO, # Level: Which level of records will be kept.
            #INFO: Normal operating information
            # Timestamp requirement
            format='%(asctime)s | %(message)s', # format: The format in which records are displayed
            datefmt='%Y-%m-%d %H:%M:%S' # datefmt: Date-time format.
        )

        # It accepts normal client connections
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(backlog)

        # It accepts relay connections.
        self.relay_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.relay_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.relay_server.bind((host, 6000))
        self.relay_server.listen(backlog)

        # Catch keyboard interrupts
        signal.signal(signal.SIGINT, self.sighandler)

    def sighandler(self, signum, frame):
        """Clean up client outputs."""
        print("Shutting down server...")
        # Close existing client sockets
        for output in self.outputs:
            output.close()
        self.server.close()
        self.relay_server.close()
        sys.exit(0)

    def get_client_name(self, client):
        """Return the name of the client."""
        info = self.clientmap[client]
        host, name = info[0][0], info[1]
        return '@'.join((name, host))


    # monitoringe bilgi göderiyoruz
    def send_monitor_event(self, event):
        with self.monitor_lock:
            self.monitor_socket.send(event)

    def run(self):
        print("Chat Server listening on ports 5000 and 6000")
        threading.Thread(
            target=self.accept_clients,
            args=(self.server, False),
            daemon=True
        ).start()

        threading.Thread(
            target=self.accept_clients,
            args=(self.relay_server, True),
            daemon=True
        ).start()

        threading.Event().wait()

    # Multiple clients can connect simultaneously
    def accept_clients(self, server_socket, is_relay):
        while True:
            client, address = server_socket.accept()

            client_thread = threading.Thread(
                target=self.handle_client,
                args=(client, address, is_relay)
            )
            client_thread.start()

    #benzersiz nickname atama için
    def assign_nickname(self, requested_name, is_relay=False):
        with self.lock: # for concurrency
            #We will reject the connection if the nickname starts with * and the connection is not relay.
            if requested_name.startswith('*') and not is_relay:
                return None

            if requested_name not in self.usernames: #Each user's nickname is unique.
                self.usernames.append(requested_name)
                return requested_name

            counter = 1

            # If the same nickname is desired, a number is added to the end.
            while f"{requested_name}{counter}" in self.usernames:
                counter += 1

            new_name = f"{requested_name}{counter}"
            self.usernames.append(new_name)

            return new_name




    def handle_client(self, client, address, is_relay=False):
        try:
            # We obtain the user's nickname information
            data = receive(client)

            if not data or not data.startswith('NAME: '):
                logging.warning(
                    "INVALID_REGISTRATION | Address: %s",
                    address[0]
                )

                self.send_monitor_event(
                    "ERROR | INVALID_REGISTRATION | Address: {}".format(address[0])
                )
                return

            requested_name = data.split('NAME: ', 1)[1]

            cname = self.assign_nickname(requested_name, is_relay)

            if cname is None:
                logging.warning(
                    "INVALID_NICKNAME | Requested name: %s",
                    requested_name
                )

                with self.lock:
                    send(client, 'ERROR: Nickname cannot start with *')

                self.send_monitor_event(
                    "ERROR | INVALID_NICKNAME | Requested name: {}".format(requested_name)
                )

                return
            # We add the user to the server's records.
            with self.lock:
                self.clients += 1
                self.clientmap[client] = (address, cname) # We hide both the IP/port and the nickname
                self.outputs.append(client) #We add the connecting client to the outputs list.
                # This allows the server to track the connection.

                # We record the user's connection to the server in the log file.
                logging.info( # Creates records at the INFO level.
                    "CONNECT | User: %s | Address: %s", # It indicates that the event is connected.
                    cname, # The nickname of the connected user.
                    address[0] # The user's IP address.

                    # address[0] → IP address (192.168.1.10)
                    # address[1] → Port number (54321)
                )

                # We transmit the connection event to the monitoring system.
                self.send_monitor_event(
                    "CONNECT | User: {} | Address: {}".format(cname, address[0])
                )

                # The server sends the client its IP address and assigned nickname.
                send(client, 'CLIENT: ' + str(address[0]))
                send(client, 'NICKNAME: ' + cname) # The server sends the assigned nickname to the client.

                # We send the list of connected users to the new user.
                send(client, 'USERLIST: ' + ','.join(self.usernames))

                # Notification message for new connection
                msg = "\n(Connected: New client ({}) from {})".format(
                    self.clients, self.get_client_name(client)
                )

                for output in self.outputs:
                    if output != client:
                        send(output, msg)

                # User lists are kept up-to-date on all clients.
                for output in self.outputs:
                    send(output, 'USERLIST: ' + ','.join(self.usernames)) # We send the updated nickname list to all clients.



            # 4. Kullanıcıdan gelen mesajları sürekli dinle
            while True:
                data = receive(client)
                if not data:
                    break

                # Rate limiting kontrolü
                current_time = time.time()

                with self.lock:
                    if client not in self.message_times:
                        self.message_times[client] = []

                    # This means the muted user will be blocked before the message count check is complete.
                    if time.time() < self.muted_until.get(client, 0):
                        continue

                    # Delete messages older than the last 10 seconds.
                    self.message_times[client] = [
                        t for t in self.message_times[client]
                        if current_time - t < 10
                    ]

                    # We are checking the limit of 6 messages per 10 seconds.
                    if len(self.message_times[client]) >= 5: # Sending 5 messages in the last 10 seconds will block new messages.
                        self.muted_until[client] = time.time() + 10
                        # We set the user's mute end time to 10 seconds after the current time.
                        logging.warning(
                            "RATE_LIMIT | User: %s",
                            self.get_client_name(client)
                        )
                        self.send_monitor_event(
                            "RATE_LIMIT | User: {}".format(self.get_client_name(client))
                        )
                        # rate limiting notification
                        send(client, "ERROR: Message limit exceeded. You are muted for 10 seconds.")

                        # The message processing codes below are skipped with the 'continue' statement.
                        continue

                    self.message_times[client].append(current_time)

                # Private mesaj kontrolü
                if data.startswith('/msg '): # Clients can send private messages using the /msg command.
                    parts = data.split(' ', 2)

                    # We will send an error message if the command was used incorrectly.
                    #  # The server actually expects this format : /msg nickname message

                    if len(parts) < 3:
                        logging.warning(
                            "INVALID_COMMAND | User: %s",
                            self.get_client_name(client)
                        )

                        send(client, "ERROR: Usage: /msg nickname message")

                        self.send_monitor_event(
                            "ERROR | INVALID_COMMAND | User: {}".format(
                                self.get_client_name(client)
                            )
                        )
                        continue

                    target_name = parts[1] # parts[1] → Bengisu (target user)
                    private_message = parts[2] # parts[2] → Hi! (message)

                    with self.lock:
                        target_client = None

                        # Find the target user's connection.
                        for connected_client, info in self.clientmap.items():
                            if info[1] == target_name:
                                target_client = connected_client
                                break

                        if target_client is None:
                            logging.warning(
                                "PRIVATE_FAILED | Sender: %s | Recipient: %s | Reason: User offline",
                                self.get_client_name(client),
                                target_name
                            )

                            send(client, "ERROR: User is not online.")

                            self.send_monitor_event(
                                "ERROR | Private message recipient is offline: {}".format(target_name)
                            )
                            continue

                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # The server is generating a timestamp.

                        # message creation
                        private_msg = "[{}] [Private] [{}] >> {}".format(
                            timestamp, # adding timestamp
                            self.get_client_name(client), # We add the sender's nickname to the message.
                            private_message
                        )

                        # Private mesajı yalnızca hedef kullanıcıya gönder
                        send(target_client, private_msg)

                        # Private messages are saved to the log file.
                        logging.info(
                            "PRIVATE | Sender: %s | Recipient: %s | Message: %s", # Recipient → Mesajın alıcısı.
                            self.get_client_name(client),
                            target_name,
                            private_message
                        )

                        self.send_monitor_event(
                            "PRIVATE | Sender: {} | Recipient: {} | Message: {}".format(
                                self.get_client_name(client),
                                target_name,
                                private_message
                            )
                        )

                        # We send a confirmation message to the sender that the message has been delivered.
                        send(client, "Private message sent to {}".format(target_name))

                    continue

                # server-side timestamp generation
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                """
                We create the message in three parts:
                    - timestamp: Time of sending.
                    -self.get_client_name(client): Sender's nickname. 
                    - data: Message content.
                """
                msg = "[{}] #[{}]>>{}".format(
                    timestamp,
                    self.get_client_name(client),
                    data
                )

                # We log the public message to the log file.
                logging.info(
                    "PUBLIC | Sender: %s | Message: %s",
                    self.get_client_name(client),
                    data
                )

                self.send_monitor_event(
                    "PUBLIC | Sender: {} | Message: {}".format(
                        self.get_client_name(client),
                        data
                    )
                )

                # We send the public message to all users.
                with self.lock:
                    for output in self.outputs: # self.outputs: List of connected clients.
                        send(output, msg)

        except socket.error as e:
            print("Socket error: {}".format(e))

            # logging.exception() → Writes the error and its details to the log file.
            logging.exception("SOCKET ERROR")

            self.send_monitor_event(
                "SOCKET ERROR | {}".format(e)
            )

        finally:
            #  We clear the user's records when they leave.
            with self.lock:
                info = self.clientmap.pop(client, None)
                # We remove the disconnecting client from the clientmap dictionary using pop.

                if client in self.outputs:
                    self.outputs.remove(client)
                    # We remove the client from the list of connected connections using the remove function.

                if info:
                    address, cname = info

                    # We log the connection interruption event to the log file.
                    logging.info(
                        "DISCONNECT | User: %s | Address: %s",
                        cname,
                        address[0]
                    )
                    # self.send_monitor_event()` then transmits this interruption event to the monitoring system.
                    self.send_monitor_event(
                        "DISCONNECT | User: {} | Address: {}".format(cname, address[0])
                    )

                    # User lists are up-to-date on all clients.
                    if cname in self.usernames:
                        self.usernames.remove(cname)

                    # We then send the updated list to the remaining clients.
                    for output in self.outputs:
                        send(output, 'USERLIST: ' + ','.join(self.usernames))


                    self.clients -= 1

                    # When a user leaves, other users receive a notification.
                    msg = "\n(Now hung up: Client from {})".format(
                        cname + '@' + address[0]
                    )

                    for output in self.outputs:
                        try:
                            send(output, msg)
                        except socket.error:
                            pass

            client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chat Server')
    parser.add_argument('--host', type=str, default='localhost',help='IP address to listen on')
    parser.add_argument('--port', type=int, default=5000, help='Port number to listen on')
    args = parser.parse_args()

    server = ChatServer(args.port, args.host)
    server.run()

# python 03-SimpleChatServer.py --port=8800

# Sıralamamız şu:
# 1. Kullanıcı Bengisu nickname'ini istedi.
# 2. assign_nickname() bu ismin kullanımda olup olmadığını kontrol etti.
# 3. Kullanımda değilse usernames listesine ekledi. Kullanımdaysa Bengisu1 gibi yeni bir isim oluşturdu.
# 4. Kesinleşen nickname'i handle_client() metoduna döndürdü.
# 5. handle_client() da bu nickname'i clientmap sözlüğüne kaydetti.

"""
send() → Sends data.

append() → Adds data to the list.

logging.info() → Records data to the log file.
"""