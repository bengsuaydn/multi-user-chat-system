
#!/usr/bin/env python3

import socket
import struct
import pickle
import threading
import argparse


def send(channel, message):
    buffer = pickle.dumps((message,))
    value = socket.htonl(len(buffer))
    size = struct.pack("L", value)

    channel.sendall(size)
    channel.sendall(buffer)


def receive_exact(channel, size):
    data = b''

    while len(data) < size:
        part = channel.recv(size - len(data))

        if not part:
            return None

        data += part

    return data


def receive(channel):
    header_size = struct.calcsize("L")

    size_data = receive_exact(channel, header_size)

    if size_data is None:
        return None

    size = socket.ntohl(struct.unpack("L", size_data)[0])

    buffer = receive_exact(channel, size)

    if buffer is None:
        return None

    try:
        return pickle.loads(buffer)[0]
    except (pickle.PickleError, IndexError, TypeError):
        return None


def close_connections(client, server):
    for connection in (client, server):
        try:
            connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass


def forward_data(source, destination, client, server):
    try:
        while True:
            data = source.recv(4096)

            if not data:
                break

            destination.sendall(data)

    except OSError:
        pass

    finally:
        close_connections(client, server)


def handle_client(client, address, server_host, server_port):
    server = None

    try:
        # Connect to Main Chat Server
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect((server_host, server_port))

        # Read the client's initial registration
        registration = receive(client)

        if not isinstance(registration, str):
            return

        if not registration.startswith('NAME: '):
            return

        requested_name = registration.split('NAME: ', 1)[1]

        # Reject nicknames beginning with *
        if requested_name.startswith('*'):
            send(client, 'ERROR: Nickname cannot start with *')
            return



        # Add exactly one leading *
        relayed_registration = 'NAME: ' + '*' + requested_name

        # Forward registration to Main Server
        send(server, relayed_registration)

        print("Registered relay user:", '*' + requested_name)

        # Forward data in both directions
        client_to_server = threading.Thread(
            target=forward_data,
            args=(client, server, client, server),
            daemon=True
        )

        server_to_client = threading.Thread(
            target=forward_data,
            args=(server, client, client, server),
            daemon=True
        )

        client_to_server.start()
        server_to_client.start()

        client_to_server.join()
        server_to_client.join()

    except OSError as e:
        print("Relay error:", e)

    finally:
        if server is not None:
            server.close()

        client.close()

        print("Connection closed:", address)


def start_relay(host, port, server_host, server_port):
    relay = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    relay.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    relay.bind((host, port))
    relay.listen(5)

    print("Relay listening on {}:{}".format(host, port))

    try:
        while True:
            client, address = relay.accept()

            client_thread = threading.Thread(
                target=handle_client,
                args=(client, address, server_host, server_port),
                daemon=True
            )

            client_thread.start()

    except KeyboardInterrupt:
        print("Relay shutting down...")

    finally:
        relay.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chat Relay Server')

    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=7000)
    parser.add_argument('--server-host', default='localhost')
    parser.add_argument('--server-port', type=int, default=6000)

    args = parser.parse_args()

    start_relay(
        args.host,
        args.port,
        args.server_host,
        args.server_port
    )
