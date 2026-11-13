# Test Documentation

This document describes the tests performed to verify the functionality of the Multi-User Chat System.

All tests were performed using Python clients and the server components.

## T01 – Public Chat

Two Python clients were connected to the chat server. Public messages were exchanged in both directions.

**Verified:**
- Messages were delivered to all connected clients.
- Messages displayed timestamps and assigned nicknames.
- The connected user list was updated correctly.

## T02 – Private Chat

Private messages were exchanged between two Python clients using the `/msg` command. A third client was used to verify message privacy.

**Verified:**
- Private messages were delivered only to the intended recipient.
- Other connected clients could not see private message content.
- Sending a message to a disconnected user returned an error.

## T03 – Nickname Validation

Two clients connected using the same requested nickname. A separate connection attempt tested nicknames beginning with `*`.

**Verified:**
- Duplicate nicknames were automatically assigned unique names.
- Direct clients could not register with nicknames beginning with `*`.

## T04 – Client Disconnection

Clients were disconnected using the Exit command and by normally closing the client application.

**Verified:**
- Disconnected clients were removed from the server's records.
- The user list was updated for remaining clients.
- The chat server continued running and accepting connections.

## T05 – Rate Limiting

A Python client sent multiple messages rapidly to trigger the rate-limiting mechanism.

**Verified:**
- The configured message limit was enforced.
- The client was temporarily muted for 10 seconds.
- The rate-limit event was recorded and transmitted to the monitoring system.

## T06 – Logging and Live Monitoring

The local log file (`chat_server.txt`) and the monitoring dashboard were checked. Public and private messages were sent while observing the dashboard.

**Verified:**
- Server events were recorded in the local log file with timestamps.
- Events were transmitted to the Monitoring Server through WebSocket communication.
- The dashboard displayed live events and updated user and message counters without manual refresh.
- A message sent to multiple users increased the message counter only once.
- Closing the monitoring page did not interrupt chat communication.

## T07 – Relay Communication

A Python client connected to the chat server through the relay. Communication was tested between the relayed client and a directly connected client.

**Verified:**
- The relayed client received a nickname with the `*` prefix.
- The relayed client could exchange messages with a direct client.
- Disconnecting the relayed client triggered connection cleanup.

## Test Evidence

Screenshots and supporting test evidence are stored in this directory.

The server log file is located in the project root directory as `chat_server.txt`.