import socket
import sys
import time

class SimpleTCPClient:
    def __init__(self, host: str = 'localhost', port: int = 6379):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def send_command(self, command: str) -> str:
        try:
            self.socket.send((command + '\n').encode('utf-8'))
            response = self.socket.recv(4096).decode('utf-8').strip()
            return response
        except Exception as e:
            return f"ERROR: {e}"

    def send_raw(self, raw_command: str) -> str:
        """Send raw RESP command"""
        try:
            # raw_command is expected to contain \r\n literals as escape sequences,
            # so convert them to actual newlines first
            processed = raw_command.encode('utf-8').decode('unicode_escape')
            self.socket.send(processed.encode('utf-8'))
            response = self.socket.recv(4096).decode('utf-8').strip()
            return response
        except Exception as e:
            return f"ERROR: {e}"

    def interactive_mode(self):
        print("Interactive mode. Type 'quit' or 'exit' to exit.")
        print("Supported commands: SET key value [EX seconds], GET key")
        print("To send raw RESP command, type: raw <RESP command>")
        print(r"Example raw command: raw *3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n")
        while True:
            try:
                command = input(f"{self.host}:{self.port}> ").strip()
                if not command:
                    continue
                if command.lower() in ('exit', 'quit'):
                    break
                if command.lower().startswith("raw "):
                    raw_cmd = command[4:].strip()
                    response = self.send_raw(raw_cmd)
                else:
                    response = self.send_command(command)
                print(response)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                break

    def benchmark_mode(self):
        print("Benchmark mode: testing SET/GET with large keys and values")

        def generate_large_data(size_kb):
            return 'x' * (size_kb * 1024)

        key_sizes = [1, 5, 10]  # KB
        value_sizes = [10, 50, 100]  # KB
        repeat = 5

        for key_kb in key_sizes:
            for val_kb in value_sizes:
                key = generate_large_data(key_kb)
                value = generate_large_data(val_kb)

                total_set = 0
                total_get = 0

                for _ in range(repeat):
                    # SET
                    start = time.time()
                    self.socket.send((f"SET {key} {value}\n").encode('utf-8'))
                    self.socket.recv(4096)
                    total_set += (time.time() - start)

                    # GET
                    start = time.time()
                    self.socket.send((f"GET {key}\n").encode('utf-8'))
                    self.socket.recv(4096)
                    total_get += (time.time() - start)

                print(f"\n Key: {key_kb}KB | Value: {val_kb}KB | Repeats: {repeat}")
                print(f"   Avg SET Time: {total_set/repeat:.6f}s")
                print(f"   Avg GET Time: {total_get/repeat:.6f}s")

    def close(self):
        if self.socket:
            self.socket.close()


def main():
    client = SimpleTCPClient()
    if not client.connect():
        sys.exit(1)

    mode = input("Enter mode (interactive/benchmark): ").strip()
    if mode == "benchmark":
        client.benchmark_mode()
    else:
        try:
            client.interactive_mode()
        finally:
            client.close()


if __name__ == "__main__":
    main()
