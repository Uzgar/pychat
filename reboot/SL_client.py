import tkinter as tk
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

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
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Server List")
        self.geometry("400x300")

        self.server_listbox = tk.Listbox(self, height=10, width=50)
        self.server_listbox.pack(padx=10, pady=10)

        self.connect_button = tk.Button(self, text="Connect", command=self.connect_to_server)
        self.connect_button.pack(pady=10)

    def connect_to_server(self):
        selected_server = self.server_listbox.get(tk.ACTIVE)
        if selected_server:
            self.parent.connect_to_server(selected_server)

class ClientGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Chat Client")

        self.username_dialog = PseudonymDialog(self.master)
        self.master.wait_window(self.username_dialog)

        self.pseudonym = self.username_dialog.pseudonym

        self.server_list_page = ServerListPage(self.master)
        self.server_list_page.protocol("WM_DELETE_WINDOW", self.master.destroy)

        # Uncomment the following line to use server discovery
        # self.discover_servers()

        self.servers = ["192.168.137.145", "192.168.1.100", "192.168.0.1"]  # Replace with your server IPs
        for server in self.servers:
            self.server_list_page.server_listbox.insert(tk.END, server)

    def discover_servers(self):
        self.server_list_page.server_listbox.delete(0, tk.END)
        self.server_list_page.server_listbox.insert(tk.END, "Discovering servers...")

        # Create a socket for discovery
        discovery_socket = socket(AF_INET, SOCK_STREAM)
        discovery_socket.settimeout(2)  # Set a timeout for server discovery

        try:
            discovery_socket.connect(("localhost", 5566))  # Replace with your server's IP and port
            discovery_socket.sendall("DISCOVER".encode('utf-8'))

            data = discovery_socket.recv(1024).decode('utf-8')
            if data.startswith("DISCOVERY_RESPONSE:"):
                server_list = data.split(":")[1].split(", ")
                self.server_list_page.server_listbox.delete(0, tk.END)
                for server in server_list:
                    self.server_list_page.server_listbox.insert(tk.END, server)
        except Exception as e:
            print(f"Error during server discovery: {e}")
        finally:
            discovery_socket.close()

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

def main():
    root = tk.Tk()
    client_gui = ClientGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
