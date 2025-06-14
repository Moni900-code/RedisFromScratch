import socket
import logging

# Setup client logging
logging.basicConfig(
    filename='client_resp.log',
    filemode='a',
    format='%(asctime)s | %(message)s',
    level=logging.DEBUG
)

def encode_resp(args):
    resp = f"*{len(args)}\r\n"
    for arg in args:
        arg = str(arg)
        resp += f"${len(arg)}\r\n{arg}\r\n"
    logging.debug(f"Encoded request: {repr(resp)}")
    return resp.encode('utf-8')

def decode_resp(data):
    logging.debug(f"Received raw: {repr(data)}")
    lines = data.split("\r\n")
    if not lines:
        return "(empty)"
    prefix = lines[0][0]
    if prefix == '+':
        return lines[0][1:]
    elif prefix == '-':
        return f"ERROR: {lines[0][1:]}"
    elif prefix == '$':
        if lines[0] == "$-1":
            return "nil"
        if len(lines) > 1:
            return lines[1]
        return "(incomplete bulk string)"
    return data


class SimpleRESPClient:
    def __init__(self, host='localhost', port=6379):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        print(f"Connected to {self.host}:{self.port}")

    def send_command(self, args):
        payload = encode_resp(args)
        self.socket.send(payload)
        data = self.socket.recv(4096).decode('utf-8')
        return decode_resp(data)

    def interactive_mode(self):
        print("Interactive mode. Type 'quit' or 'exit' to exit.")
        print("Supported commands: SET key value, GET key, EXPIRE key seconds, BENCHMARK count")
        while True:
            try:
                cmd = input(f"{self.host}:{self.port}> ").strip()
                if not cmd:
                    continue
                if cmd.lower() in ('exit', 'quit'):
                    break
                args = cmd.split()
                resp = self.send_command(args)
        
                print(resp)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                break

    def benchmark_mode(self):
        print("Benchmark mode: testing SET/GET with large keys and values")

        def generate_large_data(size_kb):
            return 'x' * (size_kb * 1024)

        key_sizes = [1, 5, 10]         # KB
        value_sizes = [10, 50, 100]    # KB
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
                    self.send_command(['SET', key, value])
                    total_set += (time.time() - start)

                    # GET
                    start = time.time()
                    self.send_command(['GET', key])
                    total_get += (time.time() - start)

                print(f"\n Key: {key_kb}KB | Value: {val_kb}KB | Repeats: {repeat}")
                print(f"   Avg SET Time: {total_set/repeat:.6f}s")
                print(f"   Avg GET Time: {total_get/repeat:.6f}s")


if __name__ == "__main__":
    client = SimpleRESPClient()
    client.connect()
    try:
        mode = input("Enter mode (interactive/benchmark): ").strip()
        if mode == "benchmark":
            client.benchmark_mode()
        else:
            client.interactive_mode()
    finally:
        client.close()
