#!/usr/bin/env python3
import select
import socket
import sys
import signal
import pickle
import struct
import argparse
import threading

SERVER_HOST = 'localhost'
CHAT_SERVER_NAME = 'server'

# Some utilities (assumed to be used by both server and client)
def send(channel, *args):
    buffer = pickle.dumps(args)
    value = socket.htonl(len(buffer))
    size = struct.pack("L", value)
    channel.send(size)
    channel.send(buffer)

def receive(channel):
    size_data = channel.recv(struct.calcsize("L"))
    try:
        size = socket.ntohl(struct.unpack("L", size_data)[0])
    except struct.error as e:
        return ''
    buf = b""
    while len(buf) < size:
        buf += channel.recv(size - len(buf))
    return pickle.loads(buf)[0]

class ChatClient:
    """A command line chat client using a separate input thread."""
    def __init__(self, name, port, host=SERVER_HOST):
        self.name = name
        self.connected = False
        self.host = host
        self.port = port
        # Initial prompt
        self.prompt = '[' + '@'.join((self.name, socket.gethostname().split('.')[0])) + ']> '
        # Connect to server at port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, self.port))
            print("Now connected to chat server @ port {}".format(self.port))
            self.connected = True
            # Send my name...
            send(self.sock, 'NAME: ' + self.name)

            # Bu kod, sunucunun bize gönderdiği IP adresini ve atanmış nickname'i alıp değişkenlere kaydediyor.
            client_data = receive(self.sock)

            if not client_data or client_data.startswith('ERROR:'):
                print(client_data or "Connection closed by server.")
                self.sock.close()
                sys.exit(1)

            nickname_data = receive(self.sock)
            userlist_data = receive(self.sock)

            addr = client_data.split('CLIENT: ')[1]
            self.name = nickname_data.split('NICKNAME: ')[1]

            # Bu satır, server'dan gelen kullanıcı isimlerini Python listesine dönüştürür.
            self.usernames = userlist_data.split('USERLIST: ')[1].split(',')

            self.prompt = '[' + '@'.join((self.name, socket.gethostname().split('.')[0])) + ']> '


        except socket.error as e:
            print("Failed to connect to chat server @ port {}".format(self.port))
            sys.exit(1)

    def run(self):
        """Chat client main loop using a separate input thread."""
        def input_thread():


            # This thread handles user input from the console.
            while self.connected:
                line = sys.stdin.readline().strip()
                if line:
                    if line.lower() == 'exit': # Artık kullanıcı exit yazdığında bağlantı kapatılacak.
                        self.connected = False
                        self.sock.shutdown(socket.SHUT_RDWR)
                        self.sock.close()
                        break

                    send(self.sock, line)

        # Start the input thread
        t = threading.Thread(target=input_thread, daemon=True)
        t.start()

        try:
            # Main thread: receive messages from the server.
            while self.connected:
                data = receive(self.sock)
                if not data:
                    print("Client shutting down.")
                    self.connected = False
                    break

                else:

                    if data.startswith('USERLIST: '): # Print received messages
                        userlist = data.split('USERLIST: ', 1)[1]
                        self.usernames = userlist.split(',') if userlist else []
                        print("Connected users:", self.usernames)
                        continue

                        # Print received messages
                    print("\n" + data)

                    # Optionally, reprint the prompt:
                    sys.stdout.write(self.prompt)
                    sys.stdout.flush()
        except KeyboardInterrupt:
            print("Client interrupted.")
        finally:
            self.sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Multi-User Chat Client')
    parser.add_argument('--name', required=True)
    parser.add_argument('--host', required=True)
    parser.add_argument('--port', type=int, required=True)

    args = parser.parse_args()

    client = ChatClient(name=args.name, port=args.port, host=args.host)
    client.run()


# python 03-SimpleChatClient.py --name=client1 --port=8800
# python 03-SimpleChatClient.py --name=client2 --port=8800
