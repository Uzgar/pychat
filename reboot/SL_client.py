import tkinter as tk
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, SO_BROADCAST, SOL_SOCKET
from threading import Thread, Event

class PseudonymDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Enter Pseudonym")
        self.geometry("300x100")

        self.label = tk.Label(self, text="Choose a pseudonym:")
        self.label.pack(pady=10)

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.entry_var, width=20)
        self.entry.pack(pady=10)

        self.ok_button = tk.Button(self, text="OK", command=self.ok_button_click)
        self.ok_button.pack()

    def ok_button_click(self):
        self.pseudonym = self.entry_var.get()
        self.destroy()

class ServerListPage(tk.Toplevel):
    def __init__(self, parent, client_gui):
        super().__init__(parent)
        self.title("Server List")
        self.geometry("400x300")

        self.client_gui = client_gui  # Store a reference to the ClientGUI instance

        self.server_listbox = tk.Listbox(self, height=10, width=50)
        self.server_listbox.pack(padx=10, pady=10)

        self.connect_button = tk.Button(self, text="Connect", command=self.connect_to_server)
        self.connect_button.pack(pady=10)

    def connect_to_server(self):
        selected_server = self.server_listbox.get(tk.ACTIVE)
        if selected_server:
            self.client_gui.connect_to_server(selected_server)

class ClientGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Chat Client")

        self.username_dialog = PseudonymDialog(self.master)
        self.master.wait_window(self.username_dialog)

        self.pseudonym = self.username_dialog.pseudonym

        # Store a reference to the ClientGUI instance in ServerListPage
        self.server_list_page = ServerListPage(self.master, client_gui=self)
        self.server_list_page.protocol("WM_DELETE_WINDOW", self.master.destroy)

        # Uncomment the following line to use server discovery
        self.discovery_event = Event()  # Event to signal completion of server discovery
        self.discover_servers()

        self.servers = ["192.168.137.145", "192.168.1.100", "192.168.0.1"]  # Replace with your server IPs
        for server in self.servers:
            self.server_list_page.server_listbox.insert(tk.END, server)

        self.discovery_event.set()  # Set the event to signal completion

    def discover_servers(self):
        broadcast_thread = Thread(target=self._discover_servers)
        broadcast_thread.start()

    def _discover_servers(self):
        broadcast_socket = socket(AF_INET, SOCK_DGRAM)
        broadcast_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        broadcast_socket.bind(("", 5566))
        broadcast_socket.sendto(b"DISCOVER_SERVERS", ("<broadcast>", 5566))

        servers = set()
        while True:
            try:
                data, addr = broadcast_socket.recvfrom(1024)
                if data == b"SERVER_FOUND":
                    servers.add(addr[0])
            except OSError:
                break

        broadcast_socket.close()
        self.update_server_list(servers)

        # Signal the main thread that discovery is complete
        self.discovery_event.set()

    def update_server_list(self, servers):
        self.server_list_page.server_listbox.delete(0, tk.END)
        for server in servers:
            self.server_list_page.server_listbox.insert(tk.END, server)

    def connect_to_server(self, selected_server):
        self.server_list_page.destroy()
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.server_address = (selected_server, 5566)
        self.sock.connect(self.server_address)

        self.sock.sendall(self.pseudonym.encode('utf-8'))

        receive_thread = Thread(target=self.receive_messages)
        receive_thread.start()

        self.setup_gui()

    def setup_gui(self):
        self.message_listbox = tk.Listbox(self.master, height=15, width=50)
        self.message_listbox.pack(padx=10, pady=10)

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(self.master, textvariable=self.entry_var, width=40)
        self.entry.pack(padx=10, pady=10)

        self.send_button = tk.Button(self.master, text="Send", command=self.send_message)
        self.send_button.pack(pady=10)

        self.users_label = tk.Label(self.master, text="Connected Users: 0")
        self.users_label.pack(side=tk.BOTTOM, padx=10, pady=10)

        self.message_listbox.insert(tk.END, f"Connected as {self.pseudonym}")

        receive_thread = Thread(target=self.receive_messages)
        receive_thread.start()

    def send_message(self):
        message = self.entry_var.get()
        self.sock.sendall(message.encode('utf-8'))
        self.message_listbox.insert(tk.END, f"{self.pseudonym}: {message}")
        self.entry_var.set("")

    def receive_messages(self):
        while True:
            try:
                data = self.sock.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                if message.startswith("USER_COUNT:"):
                    count = int(message.split(":")[1])
                    self.update_user_count(count)
                else:
                    self.message_listbox.insert(tk.END, message)
            except ConnectionError:
                break

    def update_user_count(self, count):
        self.users_label.config(text=f"Connected Users: {count}")

    def mainloop(self):
        # Wait for the discovery to complete before entering the main loop
        self.discovery_event.wait()
        self.master.mainloop()

def main():
    root = tk.Tk()
    client_gui = ClientGUI(root)
    client_gui.mainloop()

if __name__ == "__main__":
    main()
