import socket
import threading

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.servers = {"Server 1": "192.168.137.145", "Server 2": "192.168.1.100", "Server 3": "192.168.0.1"}
        self.clients = {}

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        print(f"Server listening on {self.host}:{self.port}")

        self.accept_connections()

    def accept_connections(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Accepted connection from {client_address}")

            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def handle_client(self, client_socket):
        pseudonym = client_socket.recv(1024).decode('utf-8')

        if pseudonym == "DISCOVER":
            self.send_discovery_response(client_socket)
            client_socket.close()
            return

        server_choice = self.send_server_list(client_socket)
        if server_choice not in self.servers:
            print(f"Invalid server choice from {pseudonym}")
            client_socket.close()
            return

        server_ip = self.servers[server_choice]
        print(f"{pseudonym} connected to {server_choice} at {server_ip}")

        self.clients[pseudonym] = client_socket
        self.broadcast_user_count()

        try:
            while True:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                self.broadcast_message(f"{pseudonym}: {message}")
        except ConnectionError:
            pass
        finally:
            self.remove_client(pseudonym, client_socket)

    def send_discovery_response(self, client_socket):
        server_list = list(self.servers.keys())
        server_list_str = ", ".join(server_list)
        client_socket.sendall(f"DISCOVERY_RESPONSE:{server_list_str}".encode('utf-8'))

    def send_server_list(self, client_socket):
        server_list = list(self.servers.keys())
        server_list_str = ", ".join(server_list)
        client_socket.sendall(f"SERVER_LIST:{server_list_str}".encode('utf-8'))

        choice = client_socket.recv(1024).decode('utf-8')
        return choice

    def broadcast_message(self, message):
        for client_socket in self.clients.values():
            try:
                client_socket.sendall(message.encode('utf-8'))
            except ConnectionError:
                pass

    def broadcast_user_count(self):
        count = len(self.clients)
        for client_socket in self.clients.values():
            try:
                client_socket.sendall(f"USER_COUNT:{count}".encode('utf-8'))
            except ConnectionError:
                pass

    def remove_client(self, pseudonym, client_socket):
        print(f"{pseudonym} disconnected")
        self.clients.pop(pseudonym, None)
        client_socket.close()
        self.broadcast_user_count()

def main():
    server = Server('0.0.0.0', 5566)

if __name__ == "__main__":
    main()
