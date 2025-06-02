import socket

HOST = '127.0.0.1'
PORT = 6379

data_store = {}  # In-memory key-value store

def handle_command(command: str) -> str:
    parts = command.strip().split()
    if not parts:
        return "ERR Empty command\n"

    cmd = parts[0].upper()

    if cmd == 'SET' and len(parts) == 3:
        key, value = parts[1], parts[2]
        data_store[key] = value
        return "OK\n"

    elif cmd == 'GET' and len(parts) == 2:
        key = parts[1]
        return data_store.get(key, "nil") + "\n"

    else:
        return "ERR Unknown or invalid command\n"

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"Server started on {HOST}:{PORT}")

        while True:
            conn, addr = server.accept()
            print(f"Connected by {addr}")
            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    command = data.decode()
                    response = handle_command(command)
                    conn.sendall(response.encode())

if __name__ == "__main__":
    start_server()
