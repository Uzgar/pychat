import tkinter as tk
from tkinter import filedialog
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import os

class UsernameDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Enter Username")
        self.geometry("300x100")

        self.label = tk.Label(self, text="Choose a username:")
        self.label.pack(pady=10)

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.entry_var, width=20)
        self.entry.pack(pady=10)

        self.ok_button = tk.Button(self, text="OK", command=self.ok_button_click)
        self.ok_button.pack()

    def ok_button_click(self):
        self.username = self.entry_var.get()
        self.destroy()

class ClientGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Chat Client")

        self.message_listbox = tk.Listbox(self.master, height=15, width=50)
        self.message_listbox.pack(padx=10, pady=10)

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(self.master, textvariable=self.entry_var, width=40)
        self.entry.pack(padx=10, pady=10)

        self.browse_button = tk.Button(self.master, text="Browse", command=self.browse_image)
        self.browse_button.pack(pady=10)

        self.send_button = tk.Button(self.master, text="Send", command=self.send_message)
        self.send_button.pack(pady=10)

        self.users_label = tk.Label(self.master, text="Connected Users: 0")
        self.users_label.pack(side=tk.BOTTOM, padx=10, pady=10)

        self.username_dialog = UsernameDialog(self.master)
        self.master.wait_window(self.username_dialog)

        self.username = self.username_dialog.username
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.server_address = ('192.168.144.111', 5566)  # Replace SERVER_IP with the actual IP address of your server
        self.sock.connect(self.server_address)

        # Send the chosen username to the server
        self.sock.sendall(self.username.encode('utf-8'))

        # Start the thread for receiving messages and user count
        receive_thread = Thread(target=self.receive_messages)
        receive_thread.start()

    def browse_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])
        self.entry_var.set(f"/send_image {file_path}")

    def send_message(self):
        message = self.entry_var.get()
        if message.startswith("/send_image"):
            self.send_image(message)
        else:
            self.sock.sendall(message.encode('utf-8'))
            self.display_message(f"{self.username}: {message}")
        self.entry_var.set("")

    def send_image(self, message):
        # Extract the path from the command
        path = message.split(" ")[1]
        try:
            with open(path, 'rb') as file:
                image_data = file.read()
            filename = os.path.basename(path)
            self.sock.sendall(f"/send_image {filename}".encode('utf-8'))
            self.sock.sendall(image_data)
            self.display_message(f"{self.username} sent an image: {filename}")
        except FileNotFoundError:
            self.display_message(f"Image file not found: {path}")

    def receive_messages(self):
        while True:
            try:
                data = self.sock.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                if message.startswith("USER_COUNT:"):
                    parts = message.split(":")
                    if len(parts) == 2:
                        try:
                            count = int(parts[1])
                            self.update_user_count(count)
                            continue  # Skip the rest of the loop for user count messages
                        except ValueError:
                            print("Invalid USER_COUNT message format:", message)
                            continue
                elif message.startswith("/send_image"):
                    self.receive_image()
                else:
                    self.display_message(message)
            except ConnectionError:
                break

    def display_message(self, message):
        if not message.startswith("USER_COUNT:"):
            self.message_listbox.insert(tk.END, message)

    def receive_image(self):
        try:
            filename = self.sock.recv(1024).decode('utf-8')
            image_data = self.sock.recv(1024)
            with open(filename, 'wb') as file:
                file.write(image_data)
            self.display_message(f"{self.username} sent an image: {filename}")
        except Exception as e:
            print(f"Error receiving image: {e}")

    def update_user_count(self, count):
        self.users_label.config(text=f"Connected Users: {count}")

def main():
    root = tk.Tk()
    client_gui = ClientGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
