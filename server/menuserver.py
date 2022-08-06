import http.server
import socketserver

from functools import partial

PORT = 8080
if len(sys.argv) > 1:
    PORT = int(sys.argv[1])
    
handler = partial(http.server.SimpleHTTPRequestHandler, directory="./menu")

with socketserver.TCPServer(("", PORT), handler) as http_server:
    print(http_server.server_address)
    http_server.serve_forever()
