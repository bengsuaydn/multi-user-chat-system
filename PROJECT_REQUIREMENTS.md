# Multi-User Chat System – Project Requirements

## 1. Project Overview

The goal is to develop a multi-user chat system using Python TCP sockets.

The system supports public and private messaging. Multiple users can connect and chat at the same time.

The project has four components:

- Chat Server
- Python Chat Client
- Server Monitoring Page
- Chat Relay

## 2. Chat Server

The server must:

- Accept multiple TCP client connections.
- Support configurable IP addresses and ports.
- Assign unique nicknames to connected users.
- Add a suffix if a nickname is already taken.
- Prevent direct clients from using nicknames starting with `*`.
- Accept `*` nicknames through the relay.
- Send public messages to all connected users, including the sender.
- Send private messages only to the selected recipient.
- Show an error if the recipient is offline.
- Notify users when someone joins or leaves.
- Keep the user list updated.
- Handle multiple clients using threads.
- Handle disconnections without stopping the server.
- Save messages and server events to a local log file.
- Apply a per-user message rate limit.

## 3. Python Chat Client

The client must:

- Be a separate Python application.
- Connect to the server using TCP sockets.
- Ask for a nickname and server address, or accept command-line arguments.
- Send and receive public messages.
- Send and receive private messages.
- Display message timestamps and sender nicknames.
- Display the current user list.
- Receive messages while the user is typing.
- Support an Exit command.
- Show an error when the server connection is lost.
- Support direct server connections and relay connections.

A console interface is enough.

## 4. Server Monitoring Page

The monitoring page must:

- Use HTML and JavaScript.
- Receive live events through WebSockets.
- Use a separate monitoring port from the chat server.
- Display the current number of connected chat users.
- Display the total number of processed messages.
- Show public and private message events.
- Show connection and disconnection events.
- Show errors and rate-limit events.
- Update automatically without refreshing the page.

The monitoring page must be read-only. Monitoring viewers must not appear in the chat user list.

A simple text area, list, or table is enough.

## 5. Logging and Rate Limiting

### Logging

The server must save the following events to a local text file:

- Public messages
- Private messages
- User connections
- User disconnections
- Errors
- Rate-limit events

Each message log must include its timestamp, sender, message type, and recipient when applicable.

### Rate Limiting

- Apply a message limit to each user.
- Define the allowed message count and time interval.
- Temporarily mute or disconnect users who exceed the limit.
- Notify the user about the reason.
- Record rate-limit events in the log file.

The message count must increase by one for each accepted public or private message, not for each recipient.

## 6. Message Handling and Protocol

The application must:

- Define a message format.
- Define the registration process.
- Handle fragmented TCP messages.
- Handle multiple messages received in one read.
- Define the text encoding and maximum message size.
- Validate message types and required fields.
- Reject invalid messages safely.
- Use the registered nickname as the sender identity.
- Prevent users from impersonating other users.

## 7. Concurrency and Connection Management

- Support multiple clients at the same time.
- Protect shared user data with locks.
- Protect nickname assignment and message counters.
- Prevent overlapping socket writes.
- Remove disconnected users from the server.
- Notify remaining users when someone disconnects.
- Keep the server running if one client disconnects.
- Keep the monitoring page independent from chat connections.
- Support multiple relay connections at the same time.

One thread per client is sufficient.

## 8. Chat Relay

The relay acts as an intermediary between Python clients and the main chat server.

The relay must:

- Listen on a configurable local IP address and port.
- Accept multiple Python client connections.
- Create a separate upstream connection to the main server for each client.
- Reject nicknames that already start with `*`.
- Add exactly one `*` prefix to valid nicknames.
- Forward the registration to the main server.
- Handle fragmented registration data.
- Forward the server-assigned nickname back to the client.
- Forward chat messages in both directions.
- Support multiple users concurrently.
- Close both connections when either side disconnects.
- Release associated resources after disconnection.

Monitoring connections must not pass through the relay.

## 9. Functional Tests

The following tests must be demonstrated:

| Test | Expected Result |
|---|---|
| T01 – Public Chat | Two clients exchange public messages. |
| T02 – Private Chat | Only the selected recipient receives the private message. |
| T03 – Nicknames | Duplicate names receive different nicknames. Direct clients cannot use `*`. |
| T04 – Disconnection | Disconnected users are removed. The server continues running. |
| T05 – Rate Limiting | Rapid messages trigger the configured limit. |
| T06 – Monitoring | Logs, live events, and message counts are displayed correctly. |
| T07 – Relay | Relayed users receive the `*` prefix and exchange messages with direct clients. |

Manual testing is sufficient. Screenshots and console logs can be used as evidence.

## 10. Deliverables

The final project must include:

- Chat server source code.
- Python chat client source code.
- HTML/JavaScript monitoring page.
- Chat relay source code.
- Requirements file with dependency versions.
- README with installation and execution instructions.
- Documentation of ports and configuration.
- Documentation of the message format and TCP framing.
- Documentation of concurrency and nickname handling.
- Documentation of relay connection setup.
- Documentation of the log file and rate-limit policy.
- Screenshots or logs for tests T01–T07.

## 11. Important Notes

- Python TCP sockets must be used for chat communication.
- WebSockets must only be used for server monitoring.
- A browser-based chat client is not required.
- A simple console client is enough.
- A simple monitoring page is enough.
- A database is not required.
- Automated tests are not required.
- Advanced security features are not required.