# Multi-User Chat System

A TCP-based multi-user chat application developed in Python. The system supports public messaging, private messaging, nickname management, rate limiting, message logging, live monitoring, and communication through an optional relay server.

## Features

- **Public Chat:** Send messages to all connected clients.
- **Private Messaging:** Send messages to a specific user using `/msg`.
- **Nickname Management:** Assign unique nicknames to connected clients.
- **Rate Limiting:** Limit message frequency to prevent excessive messaging.
- **Connection Management:** Handle client connections and disconnections.
- **Logging:** Record chat events and errors in a log file.
- **Live Monitoring:** Display connected user and message counts through a web dashboard.
- **Relay Server:** Allow clients to connect through an intermediary server.

## Technologies

- Python
- TCP Socket Programming
- Multithreading
- WebSocket
- HTML
- Python Logging
- Pickle and Struct

## Project Structure

```text
multi-user-chat-system/
├── client/
│   └── chat_client.py
├── server/
│   └── chat_server.py
├── relay/
│   └── relay.py
├── monitoring/
│   ├── dashboard.html
│   └── monitor_server.py
├── tests/
│   ├── README-TESTS.md
│   ├── T01/
│   ├── T02/
│   ├── T03/
│   ├── T04/
│   ├── T05/
│   ├── T06/
│   └── T07/
├── PROJECT_REQUIREMENTS.md
├── chat_server.txt
└── README.md
```

## Installation

Clone or download the project and navigate to its directory:

```bash
cd multi-user-chat-system
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the required third-party dependency:

```bash
pip install websockets
```

## Running the Application

The servers should be started in the following order.

### 1. Start the Monitoring Server

Open a terminal and run:

```bash
python monitoring/monitor_server.py
```

The monitoring server provides:

- HTTP dashboard: `http://localhost:8000`
- WebSocket connection: `ws://localhost:8765`

Open the dashboard in a browser:

```text
http://localhost:8000
```

### 2. Start the Main Chat Server

Open another terminal and run:

```bash
python server/chat_server.py
```

The main chat server uses:

| Port | Purpose |
|---|---|
| 5000 | Direct client connections |
| 6000 | Relay server connections |

The monitoring server must be running before the main chat server starts because the chat server establishes a WebSocket connection during initialization.

### 3. Connect a Client

Open another terminal for each client and run:

```bash
python client/chat_client.py --name Ali --host localhost --port 5000
```

For another client, use a different nickname:

```bash
python client/chat_client.py --name Ayse --host localhost --port 5000
```

Multiple clients can connect to the chat server simultaneously.

## Using the Chat

### Public Messages

Type a message directly into the client terminal to send it to all connected users.

### Private Messages

Use the following command:

```text
/msg nickname message
```

Example:

```text
/msg Ayse Hello!
```

The message is delivered only to the specified recipient.

### Disconnecting

Type the following command to leave the chat:

```text
exit
```

## Rate Limiting

The server applies a rate limit to messages sent by each client.

- A client can send up to 5 messages within 10 seconds.
- If the limit is exceeded, the client is muted for 10 seconds.

## Logging and Monitoring

### Logging

Chat server events are recorded in:

```text
chat_server.txt
```

The log file includes connection events, disconnections, public and private messages, nickname-related events, rate-limit events, and errors.

### Live Monitoring

The monitoring dashboard displays:

- Current connected user count
- Total public and private message count
- Live chat events

The dashboard receives updates through a WebSocket connection. Public and private messages are counted once per message, not once per recipient.

## Relay Server (Optional)

The relay server allows clients to connect to the main chat server through an intermediary connection.

### 1. Start the Relay Server

After starting the main chat server, open another terminal and run:

```bash
python relay/relay.py
```

The relay server listens on port `7000` and forwards client connections to the main chat server on port `6000`.

### 2. Connect Through the Relay Server

Run the client using port `7000`:

```bash
python client/chat_client.py --name Ali --host localhost --port 7000
```

Clients connecting through the relay server receive a `*` prefix in their assigned nicknames.

For example:

```text
*Ali
```

## Testing

The project was tested using seven test cases:

- T01 – Public Chat
- T02 – Private Chat
- T03 – Nickname Management
- T04 – Client Disconnection
- T05 – Rate Limiting
- T06 – Logging and Live Monitoring
- T07 – Relay Server

Test descriptions and screenshots are available in the `tests/` directory.

See [tests/README-TESTS.md](tests/README-TESTS.md) for details.

## Project Requirements

For the detailed project requirements, see [PROJECT_REQUIREMENTS.md](PROJECT_REQUIREMENTS.md).