import socket
from threading import Thread
import time

Login_info = [
    ['max', '0000'],
    ['kik', '1234'],
    ['Patrice', 'Tequila'],
    ['XxTimmyGamerBoy69xX', '360noscope']
]


class Server:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (self.get_local_ip(), 5566)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(self.server_address)
        self.sock.listen(5)
        print("Server listening on", self.server_address)

        self.clients = {}  # Dictionary to store clients and their usernames
        self.blocked_ips = set()
        self.message_size_limit = 1024
        self.request_limit = 10

    def get_local_ip(self):
        return socket.gethostbyname(socket.gethostname())

    def start(self):
        user_count_thread = Thread(target=self.send_user_count)
        user_count_thread.start()

        while True:
            client_sock, client_address = self.sock.accept()
            print("Connection from", client_address)

            if client_address[0] in self.blocked_ips:
                print(f"Blocked connection attempt from {client_address}")
                client_sock.close()
                continue

            # Receive the username and password from the client
            credentials = client_sock.recv(1024).decode('utf-8')
            username, password = credentials.split(":")
            
            user_info = None
            for info in Login_info:
                if username == info[0] and password == info[1]:
                    user_info = info
                    break

            if user_info is None:
                print(f"Invalid login attempt for {username}")
                client_sock.sendall("INVALID_LOGIN".encode('utf-8'))
                client_sock.close()
                continue

            if username.lower() in ['kik', 'max']:
                print(f"{username} is an administrator.")
                self.clients[client_sock] = {'username': username, 'admin': True}
            else:
                self.clients[client_sock] = {'username': username, 'admin': False}

            client_request_count = 0
            self.broadcast_user_count()

            client_thread = Thread(target=self.handle_client, args=(client_sock, client_request_count))
            client_thread.start()

    def handle_client(self, client_sock, client_request_count):
        try:
            while True:
                data = client_sock.recv(self.message_size_limit)
                if not data:
                    break

                message = data.decode('utf-8')
                sender_username = self.clients[client_sock]['username']

                if (sender_username.lower() == 'max' or sender_username.lower() == 'kik') and message.startswith("/"):
                    command_parts = message[1:].split(" ", 1)
                    command = command_parts[0].lower()
                    target_ip = command_parts[1] if len(command_parts) > 1 else None

                    self.handle_admin_command(command, target_ip)
                else:
                    client_request_count += 1
                    if client_request_count > self.request_limit:
                        print(f"Rate limit exceeded for {self.clients[client_sock]['username']}")
                        client_sock.sendall("RATE_LIMIT_EXCEEDED".encode('utf-8'))

                        print(f"Disconnecting {self.clients[client_sock]['username']} due to rate limit exceeded.")
                        del self.clients[client_sock]
                        self.broadcast_user_count()
                        client_sock.close()
                        break

                    for other_client, username_info in self.clients.items():
                        if other_client != client_sock:
                            try:
                                if sender_username.lower() == 'max' or sender_username.lower() == 'kik':
                                    other_client.sendall(f"[Admin] : {message}".encode('utf-8'))
                                else:
                                    other_client.sendall(f"{sender_username}: {message}".encode('utf-8'))
                            except ConnectionError:
                                continue
        except ConnectionError:
            pass

        disconnected_username = self.clients.get(client_sock, {}).get('username', '')
        if disconnected_username:
            if disconnected_username.lower() == admin_username:
                disconnected_username = '[Admin]'

            admin_notification = f"{disconnected_username} left"
            for other_client, username_info in self.clients.items():
                if other_client != client_sock:
                    try:
                        other_client.sendall(admin_notification.encode('utf-8'))
                    except ConnectionError:
                        continue

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
        elif command == "announce":
            self.send_admin_announcement(target_ip)
        else:
            print("Unknown admin command")

    def send_admin_announcement(self, message):
        announcement = f"[Admin Announcement]: {message}"

        for client in self.clients:
            try:
                client.sendall(announcement.encode('utf-8'))
            except ConnectionError:
                continue

        print(f"Admin Announcement: {announcement}")

    def send_user_count(self):
        while True:
            user_count = len(self.clients)
            self.broadcast_user_count(user_count)
            time.sleep(2)

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
    server.blocked_ips = {'ip.example.tkt'}
    server.start()

if __name__ == "__main__":
    main()
