import socket
import threading
import base64
from http.server import BaseHTTPRequestHandler, HTTPServer

# Server details
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5000

# HTTP server details
HTTP_SERVER_IP = '127.0.0.1'
HTTP_SERVER_PORT = 8000

# Create a socket server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen(5)

# Store connected clients
connected_clients = []

# Thread to handle client connections
def handle_client(client_socket):
    while True:
        try:
            # Receive screen sharing data from the client
            data = client_socket.recv(4096)
            if not data:
                break

            # Arbitrate the data to all connected clients
            for client in connected_clients:
                client.sendall(data)
        except:
            break

    # Remove the client from the connected clients list
    connected_clients.remove(client_socket)
    client_socket.close()

# Thread to start the HTTP server
def start_http_server():
    class RequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><img src="/stream" /></body></html>')

        def do_HEAD(self):
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()

        def do_STREAM(self):
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()

            # Add the client socket to the connected clients list
            connected_clients.append(self.request)

            while True:
                try:
                    # Receive screen sharing data from the client
                    data = self.request.recv(4096)
                    if not data:
                        break

                    # Send the data as a multipart response
                    self.wfile.write(b'--frame\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n')
                    self.wfile.write(base64.b64encode(data))
                    self.wfile.write(b'\r\n')
                except:
                    break

            # Remove the client from the connected clients list
            connected_clients.remove(self.request)

    http_server = HTTPServer((HTTP_SERVER_IP, HTTP_SERVER_PORT), RequestHandler)
    http_server.serve_forever()

# Start the HTTP server in a separate thread
http_server_thread = threading.Thread(target=start_http_server)
http_server_thread.start()

# Accept client connections and start a new thread for each client
while True:
    client_socket, address = server_socket.accept()
    client_thread = threading.Thread(target=handle_client, args=(client_socket,))
    client_thread.start()