import tkinter as tk
from tkinter import scrolledtext
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import re
import requests
from io import BytesIO
from PIL import Image, ImageTk

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

        self.message_listbox = scrolledtext.ScrolledText(self.master, height=15, width=50, wrap=tk.WORD)
        self.message_listbox.pack(padx=10, pady=10)

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(self.master, textvariable=self.entry_var, width=40)
        self.entry.pack(padx=10, pady=10)

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

    def send_message(self):
        message = self.entry_var.get()
        self.sock.sendall(message.encode('utf-8'))
        self.message_listbox.insert(tk.END, f"{self.username}: {message}\n")
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
                    self.process_message(message)
            except ConnectionError:
                break

    def process_message(self, message):
        # Check if the message contains a URL
        url_pattern = re.compile(r'https?://\S+')
        urls = re.findall(url_pattern, message)

        if urls:
            # Display images if URLs are found
            for url in urls:
                self.display_image(url)
        else:
            # Display regular text messages
            self.message_listbox.insert(tk.END, f"{message}\n")
    
    def display_image(self, url):
        # Download the image from the URL
        response = requests.get(url)
        img_data = BytesIO(response.content)
        img = Image.open(img_data)
        img.thumbnail((50, 50))  # Adjust the size as needed

        # Convert the image to RGBA mode
        img = img.convert("RGBA")

        # Remove the alpha channel (transparency)
        img = ImageTk.PhotoImage(img)

    # Display the image in the message_listbox
        self.message_listbox.image_create(tk.END, image=img)
        self.message_listbox.insert(tk.END, '\n')  # Add another newline for better spacing
        self.message_listbox.yview(tk.END)  # Scroll to the bottom


    def update_user_count(self, count):
        self.users_label.config(text=f"Connected Users: {count}")

def main():
    root = tk.Tk()
    client_gui = ClientGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
