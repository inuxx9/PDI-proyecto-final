import socket
import threading
import tkinter as tk
from tkinter import messagebox
import configparser
import pyaudio

# ----------------------------
# Leer configuración
# ----------------------------
config = configparser.ConfigParser()
config.read('config.ini')

USERNAME = config['CHAT']['username']
MODE = config['CHAT']['mode']  # server o client
HOST = config['CHAT']['host']
PORT_CHAT = int(config['CHAT']['port_chat'])
PORT_VOICE = int(config['CHAT']['port_voice'])

# ----------------------------
# Interfaz Tkinter
# ----------------------------
root = tk.Tk()
root.title(f"Chat + Llamada ({USERNAME})")
root.geometry("450x550")

chat_log = tk.Text(root, state='disabled', wrap='word')
chat_log.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

message_entry = tk.Entry(root)
message_entry.pack(padx=10, pady=5, fill=tk.X)

# ----------------------------
# Funciones auxiliares
# ----------------------------
def log_message(msg):
    chat_log.config(state='normal')
    chat_log.insert(tk.END, msg + "\n")
    chat_log.config(state='disabled')
    chat_log.see(tk.END)

# ----------------------------
# CHAT
# ----------------------------
def handle_client(conn):
    while True:
        try:
            data = conn.recv(1024).decode()
            if not data:
                break
            log_message(data)
        except:
            break

def receive_messages(sock):
    while True:
        try:
            data = sock.recv(1024).decode()
            if not data:
                break
            log_message(data)
        except:
            break

def send_message(event=None):
    msg = message_entry.get()
    if msg.strip() == "":
        return
    full_msg = f"{USERNAME}: {msg}"
    message_entry.delete(0, tk.END)
    log_message(full_msg)
    if MODE == "server":
        for c in clients:
            c.send(full_msg.encode())
    else:
        client_socket.send(full_msg.encode())

send_btn = tk.Button(root, text="Enviar", command=send_message)
send_btn.pack(pady=5)
message_entry.bind("<Return>", send_message)

# ----------------------------
# LLAMADA DE VOZ
# ----------------------------
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
p = pyaudio.PyAudio()

def start_voice_server():
    server_voice = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_voice.bind((HOST, PORT_VOICE))
    log_message(f"[Audio] Servidor de voz escuchando en {PORT_VOICE}")

    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    output=True, frames_per_buffer=CHUNK)

    while True:
        try:
            data, addr = server_voice.recvfrom(2048)
            stream.write(data)
        except:
            break

def start_voice_client():
    client_voice = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    log_message(f"[Audio] Cliente de voz enviando a {HOST}:{PORT_VOICE}")

    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=CHUNK)

    while True:
        try:
            data = stream.read(CHUNK)
            client_voice.sendto(data, (HOST, PORT_VOICE))
        except:
            break

def start_call():
    if MODE == "server":
        threading.Thread(target=start_voice_server, daemon=True).start()
        messagebox.showinfo("Llamada", "Servidor de voz activo")
    else:
        threading.Thread(target=start_voice_client, daemon=True).start()
        messagebox.showinfo("Llamada", "Llamada iniciada")

call_btn = tk.Button(root, text="Iniciar Llamada", command=start_call, bg="#4CAF50", fg="white")
call_btn.pack(pady=10)

# ----------------------------
# RED: servidor o cliente
# ----------------------------
if MODE == "server":
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT_CHAT))
    server_socket.listen(5)
    log_message(f"Servidor de chat en {HOST}:{PORT_CHAT}")
    clients = []

    def accept_connections():
        while True:
            conn, addr = server_socket.accept()
            clients.append(conn)
            log_message(f"[Conectado] {addr}")
            threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

    threading.Thread(target=accept_connections, daemon=True).start()

else:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((HOST, PORT_CHAT))
        log_message(f"Conectado al servidor {HOST}:{PORT_CHAT}")
        threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()
    except:
        messagebox.showerror("Error", "No se pudo conectar al servidor")
        root.destroy()

# ----------------------------
root.mainloop()
