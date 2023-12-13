from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

class Server:
    def __init__(self):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.server_address = ('192.168.144.111', 5566)
        self.sock.bind(self.server_address)
        self.sock.listen(5)
        print("Server listening on", self.server_address)

        self.clients = {}  # Dictionary to store clients and their usernames

    def start(self):
        user_count_thread = Thread(target=self.send_user_count)
        user_count_thread.start()

        while True:
            client_sock, client_address = self.sock.accept()
            print("Connection from", client_address)

            # Receive the username from the client
            username = client_sock.recv(1024).decode('utf-8')
            print(f"{client_address} chose the username: {username}")

            self.clients[client_sock] = username

            # Broadcast the user count to all clients
            self.broadcast_user_count()

            client_thread = Thread(target=self.handle_client, args=(client_sock,))
            client_thread.start()

    def handle_client(self, client_sock):
        while True:
            try:
                data = client_sock.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                sender_username = self.clients[client_sock]

                if message.startswith("/send_image"):
                    self.handle_image_message(client_sock)
                else:
                    # Broadcast the message to all clients with sender's username
                    for client, username in list(self.clients.items()):
                        if client != client_sock:
                            client.sendall(f"{sender_username}: {message}".encode('utf-8'))
            except ConnectionError:
                break

        # Remove the client from the dictionary and broadcast the updated user count
        del self.clients[client_sock]
        self.broadcast_user_count()

    def handle_image_message(self, client_sock):
        try:
            filename = client_sock.recv(1024).decode('utf-8')
            image_data = client_sock.recv(1024)
            with open(filename, 'wb') as file:
                file.write(image_data)

            # Broadcast the image message to all clients
            for client in list(self.clients):
                try:
                    client.sendall(f"{self.clients[client_sock]} sent an image: {filename}".encode('utf-8'))
                except ConnectionError:
                    continue
        except Exception as e:
            print(f"Error handling image message: {e}")

    def send_user_count(self):
        while True:
            user_count = len(self.clients)
            # Broadcast the user count to all clients
            self.broadcast_user_count(user_count)

    def broadcast_user_count(self, count=None):
        if count is None:
            count = len(self.clients)

        # Créez une copie du dictionnaire avant l'itération
        clients_copy = dict(self.clients)

        for client, _ in clients_copy.items():
            try:
                client.sendall(f"USER_COUNT:{count}".encode('utf-8'))
            except ConnectionError:
                continue

def main():
    server = Server()
    server.start()

if __name__ == "__main__":
    main()
