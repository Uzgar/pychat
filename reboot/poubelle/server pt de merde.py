import socket
from threading import Thread
import time
import re

admin_username = 'kik'


class Server:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (self.get_local_ip(), 5566)

        # Enable address reuse to avoid "Address already in use" errors during development
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.sock.bind(self.server_address)
        self.sock.listen(5)
        print("Server listening on", self.server_address)

        self.clients = {}  # Dictionary to store clients and their usernames
        self.blocked_ips = set()
        self.message_size_limit = 1024
        self.request_limit = 10

    def get_local_ip(self):
        # Get the local IP address of the server
        return socket.gethostbyname(socket.gethostname())

    def start(self):
        user_count_thread = Thread(target=self.send_user_count)
        user_count_thread.start()

        while True:
            client_sock, client_address = self.sock.accept()
            print("Connection from", client_address)

            # Check if the client's IP is in the blocked list
            if client_address[0] in self.blocked_ips:
                print(f"Blocked connection attempt from {client_address}")
                client_sock.close()
                continue

            # Receive the username from the client
            username = client_sock.recv(1024).decode('utf-8')

            # Receive the password from the client
            password = client_sock.recv(1024).decode('utf-8')

            # Check if the username contains variations of 'admin'
            if self.contains_admin_variant(username):
                print(f"Blocked connection attempt with admin-like username: {username}")
                client_sock.sendall("USERNAME_BLOCKED".encode('utf-8'))
                client_sock.close()
                continue

            # Replace 'admin' with '[Admin]' for new users
            new_username = username
            if new_username.lower() == admin_username:
                new_username = '[Admin]'

            print(f"{client_address} chose the username: {new_username}")

            # Notify admin when any user joins
            admin_notification = f"{new_username} joined from {client_address}"
            for other_client, other_username in self.clients.items():
                if other_client != client_sock:
                    try:
                        other_client.sendall(admin_notification.encode('utf-8'))
                    except ConnectionError:
                        continue

            # Implement authentication logic here
            if not self.verify_login(username, password):
                print(f"Invalid login attempt for {username}")
                client_sock.sendall("INVALID_LOGIN".encode('utf-8'))
                client_sock.close()
                continue

            self.clients[client_sock] = new_username

            # Initialize the request count for the new client
            client_request_count = 0

            # Broadcast the user count to all clients
            self.broadcast_user_count()

            client_thread = Thread(target=self.handle_client, args=(client_sock, client_request_count))
            client_thread.start()

    def contains_admin_variant(self, username):
        # Check if the username contains variations of 'admin'
        admin_variants = ['admin', 'adm1n', 'adm!n']  # Add more variations as needed
        username_lower = username.lower()
        return any(variant in username_lower for variant in admin_variants)

    def handle_client(self, client_sock, client_request_count):
        try:
            while True:
                data = client_sock.recv(self.message_size_limit)
                if not data:
                    break

                message = data.decode('utf-8')
                sender_username = self.clients[client_sock]

                if sender_username.lower() == admin_username:
                    sender_username = '[Admin]'

                if sender_username == '[Admin]' and message.startswith("/"):
                    command_parts = message[1:].split(" ", 1)
                    command = command_parts[0].lower()
                    target_ip = command_parts[1] if len(command_parts) > 1 else None

                    self.handle_admin_command(command, target_ip)
                else:
                    client_request_count += 1
                    if client_request_count > self.request_limit:
                        print(f"Rate limit exceeded for {self.clients[client_sock]}")
                        client_sock.sendall("RATE_LIMIT_EXCEEDED".encode('utf-8'))

                        print(f"Disconnecting {self.clients[client_sock]} due to rate limit exceeded.")
                        del self.clients[client_sock]
                        self.broadcast_user_count()
                        client_sock.close()
                        break

                    for other_client, username in self.clients.items():
                        if other_client != client_sock:
                            try:
                                if sender_username == '[Admin]':
                                    other_client.sendall(f"[Admin]: {message}".encode('utf-8'))
                                else:
                                    other_client.sendall(f"{sender_username}: {message}".encode('utf-8'))
                            except ConnectionError:
                                continue
        except ConnectionError:
            pass  # Handle client disconnection outside the loop

        # Notify admin when any user leaves
        disconnected_username = self.clients.get(client_sock)
        if disconnected_username:
            if disconnected_username.lower() == admin_username:
                disconnected_username = '[Admin]'

            admin_notification = f"{disconnected_username} left"
            for other_client, username in self.clients.items():
                if other_client != client_sock:
                    try:
                        other_client.sendall(admin_notification.encode('utf-8'))
                    except ConnectionError:
                        continue

            for other_client, username in self.clients.items():
                if other_client != client_sock:
                    try:
                        other_client.sendall(f"{disconnected_username} has left. ".encode('utf-8'))
                    except ConnectionError:
                        continue

        # Log when a client disconnects
        if client_sock in self.clients:
            print(f"{disconnected_username} has disconnected.")
            del self.clients[client_sock]
            self.broadcast_user_count()

    def handle_admin_command(self, command, target_ip=None):
        if command == "block":
            if target_ip:
                self.blocked_ips.add(target_ip)
                print(f"Blocked IP: {target_ip}")
            else:
                print("Usage: block <ip>")
        elif command == "unblock":
            if target_ip:
                self.blocked_ips.discard(target_ip)
                print(f"Unblocked IP: {target_ip}")
            else:
                print("Usage: unblock <ip>")
        else:
            print("Unknown admin command")

    def verify_login(self, username, password):
        # Read login credentials from the file
        with open('login.txt', 'r') as file:
            for line in file:
                stored_username, stored_password = line.strip().split(', ')
                if username == stored_username and password == stored_password:
                    return True
        return False

    def send_user_count(self):
        while True:
            user_count = len(self.clients)
            # Broadcast the user count to all clients
            self.broadcast_user_count(user_count)
            time.sleep(2)  # Update user count every 5 seconds

    def broadcast_user_count(self, count=None):
        if count is None:
            count = len(self.clients)

        for client in self.clients:
            try:
                client.sendall(f"USER_COUNT:{count}".encode('utf-8'))
            except ConnectionError:
                continue


def main():
    server = Server()
    # Add IPs to the blocked list as needed
    server.blocked_ips = {'admin_ip'}  # Add the actual IP of the admin machine
    server.start()


if __name__ == "__main__":
    main()
