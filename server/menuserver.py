import http.server
import socketserver

from functools import partial

PORT = 80
handler = partial(http.server.SimpleHTTPRequestHandler, directory="./menu")

with socketserver.TCPServer(("", PORT), handler) as http_server:
    http_server.serve_forever()
