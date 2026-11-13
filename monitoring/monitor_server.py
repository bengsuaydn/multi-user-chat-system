import asyncio
import threading
import http.server
import socketserver
import websockets


# ----- HTTP SERVER (runs in separate thread) -----
class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.path = "/monitoring/dashboard.html"
        return super().do_GET()

"""Thanks to the port parameter, we can assign a different port to the function; in other words, 
the http port can be configured externally"""
def start_http_server(port=8000):
    with socketserver.TCPServer(("", port), CustomHandler) as httpd:
        print(f"HTTP server running at http://localhost:{port}")
        httpd.serve_forever()


# ----- WEBSOCKET SERVER (runs in asyncio loop)(shared messages to all) -----
connected = set()
chat_user_count = 0
message_count = 0

# Chat Server'dan gelen bir olayı, bağlı bütün monitoring sayfalarına gönderecek.
async def broadcast_event(message):
    for conn in connected.copy():
        try:
            await conn.send(message)
        except websockets.exceptions.ConnectionClosed:
            connected.discard(conn)

# Aynı görevleri koruyoruz. Sadece gelen olayın türüne bakıp sayaçları da güncelliyoruz.
async def ws_handler(websocket):
    global chat_user_count, message_count

    try:
        async for message in websocket:
            if message == "DASHBOARD":
                connected.add(websocket)

                await websocket.send(
                    "COUNTS | Users: {} | Messages: {}".format(
                        chat_user_count, message_count
                    )
                )
                continue

            if message.startswith("CONNECT |"):
                chat_user_count += 1

            elif message.startswith("DISCONNECT |"):
                chat_user_count = max(0, chat_user_count - 1)

            elif message.startswith(("PUBLIC |", "PRIVATE |")):
                message_count += 1

            await broadcast_event(message)

            await broadcast_event(
                "COUNTS | Users: {} | Messages: {}".format(
                    chat_user_count, message_count
                )
            )

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected.discard(websocket)


async def start_ws_server(port=8765): # We are configuring the web socket port
    async with websockets.serve(lambda ws: ws_handler(ws), "localhost", port):
        print(f"WebSocket server running at ws://localhost:{port}")
        await asyncio.Future()


# ----- START BOTH -----
if __name__ == "__main__":
    """Thus, we can both send port 8000 as a parameter to the HTTP Server and receive it from outside."""
    threading.Thread(
        target=start_http_server,
        args=(8000,),
        daemon=True
    ).start()

    # Default port and configurable
    asyncio.run(start_ws_server(8765))


"""HTTP Server (8000): Sends the HTML file of the monitoring page to the browser.

WebSocket Server (8765): Sends live events and counters to the monitoring page."""