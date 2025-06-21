import sys
import time
import socket

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

    def serialize_command(self, *args: str) -> str:
        """Serialize command to RESP format"""
        command = f"*{len(args)}\r\n"
        for arg in args:
            command += f"${len(arg)}\r\n{arg}\r\n"
        return command

    def parse_response(self, response: str) -> str:
        """Parse RESP response"""
        if not response:
            return "ERROR: Empty response"
        
        first_char = response[0]
        if first_char == '+':
            return response[1:-2]
        elif first_char == '-':
            return response[1:-2]
        elif first_char == '$':
            if response == "$-1\r\n":
                return "(nil)"
            parts = response.split('\r\n')
            if len(parts) < 2:
                return "ERROR: Invalid bulk string"
            return parts[1]
        else:
            return f"ERROR: Unknown response format: {response}"

    def send_command(self, *args: str) -> str:
        try:
            command = self.serialize_command(*args)
            self.socket.send(command.encode('utf-8'))
            response = self.socket.recv(4096).decode('utf-8')
            return self.parse_response(response)
        except Exception as e:
            return f"ERROR: {e}"

    def interactive_mode(self):
        print("Interactive mode. Type 'quit' or 'exit' to exit.")
        print("Supported commands: SET key value [EX seconds], GET key")
        while True:
            try:
                command = input(f"{self.host}:{self.port}> ").strip()
                if not command:
                    continue
                if command.lower() in ('exit', 'quit'):
                    break
                args = command.split()
                response = self.send_command(*args)
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
                    response = self.send_command("SET", key, value)
                    if response != "OK":
                        print(f"SET failed: {response}")
                    total_set += (time.time() - start)

                    # GET
                    start = time.time()
                    response = self.send_command("GET", key)
                    if response == "(nil)":
                        print(f"GET failed: Key not found")
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