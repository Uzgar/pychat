import tkinter as tk
from tkinter import simpledialog
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

class IPDialog(tk.simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Renseignez l'IP du serveur:").grid(row=0)
        self.ip_entry = tk.Entry(master)
        self.ip_entry.grid(row=0, column=1)
        return self.ip_entry

    def apply(self):
        self.result = self.ip_entry.get()

class UsernameDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("S'authentifier")
        self.geometry("300x200")

        self.label_username = tk.Label(self, text="Entrez votre pseudo:")
        self.label_username.pack(pady=5)

        self.entry_username_var = tk.StringVar()
        self.entry_username = tk.Entry(self, textvariable=self.entry_username_var, width=20)
        self.entry_username.pack(pady=5)

        self.label_password = tk.Label(self, text="Entrez votre mot de passe:")
        self.label_password.pack(pady=5)

        self.entry_password_var = tk.StringVar()
        self.entry_password = tk.Entry(self, textvariable=self.entry_password_var, show='*', width=20)
        self.entry_password.pack(pady=5)

        self.ok_button = tk.Button(self, text="OK", command=self.ok_button_click)
        self.ok_button.pack()

        # Lift the dialog to the top
        self.lift()

    def ok_button_click(self):
        self.username = self.entry_username_var.get()
        self.password = self.entry_password_var.get()
        self.destroy()

class ClientGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Chat Client (Miaouuu)")

        # Lift the main window to the top
        self.master.lift()

        # Ask for the server IP
        ip_dialog = IPDialog(self.master)
        self.server_ip = ip_dialog.result

        self.message_listbox = tk.Listbox(self.master, height=15, width=50)
        self.message_listbox.pack(padx=10, pady=10)

        # Create a scrollbar and attach it to the listbox
        self.scrollbar = tk.Scrollbar(self.master, command=self.message_listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.message_listbox.config(yscrollcommand=self.scrollbar.set)

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(self.master, textvariable=self.entry_var, width=40)
        self.entry.pack(padx=10, pady=10)

        self.send_button = tk.Button(self.master, text="Envoyer", command=self.send_message)
        self.send_button.pack(pady=10)

        self.users_label = tk.Label(self.master, text="Personnes en ligne : 0")
        self.users_label.pack(side=tk.BOTTOM, padx=10, pady=10)

        self.username_dialog = UsernameDialog(self.master)
        self.master.wait_window(self.username_dialog)

        self.username = self.username_dialog.username
        self.password = self.username_dialog.password
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.server_address = (self.server_ip, 5566)  # Use the provided server IP
        self.sock.connect(self.server_address)

        # Send the chosen username and password to the server
        credentials = f"{self.username}:{self.password}"
        self.sock.sendall(credentials.encode('utf-8'))

        # Start the thread for receiving messages and user count
        receive_thread = Thread(target=self.receive_messages)
        receive_thread.start()

        # Bind the Enter key to the send_message function
        self.master.bind("<Return>", lambda event: self.send_message())

    def send_message(self):
        message = self.entry_var.get()
        self.sock.sendall(message.encode('utf-8'))
        self.message_listbox.insert(tk.END, f"Vous : {message}")
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
                    # Autoscroll to the bottom of the listbox
                    self.message_listbox.yview(tk.END)
            except ConnectionError:
                break

    def update_user_count(self, count):
        self.users_label.config(text=f"Personnes connectées: {count}")

def main():
    root = tk.Tk()
    client_gui = ClientGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
