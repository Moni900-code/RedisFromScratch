import socket

HOST = '127.0.0.1'
PORT = 6379

def start_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print("Connected to server. Type SET key val or GET key.")
        try:
            while True:
                cmd = input("redis> ")
                if not cmd:
                    continue
                s.sendall(cmd.encode())
                data = s.recv(1024)
                print(data.decode().strip())
        except KeyboardInterrupt:
            print("\nExiting.")

if __name__ == "__main__":
    start_client()
