import socket
import sys
import time
import logging
from typing import Dict

# Setup logging to server_resp.log
logging.basicConfig(
    filename='server_resp.log',
    filemode='a',
    format='%(asctime)s | %(message)s',
    level=logging.DEBUG
)

class RESPParser:
    def __init__(self):
        self.buffer = ""

    def feed(self, data: str):
        self.buffer += data

    def parse(self):
        if not self.buffer or self.buffer[0] != '*':
            return None, self.buffer

        pos = self.buffer.find('\r\n')
        if pos == -1:
            return None, self.buffer

        try:
            num_elements = int(self.buffer[1:pos])
        except:
            raise ValueError("Invalid array length")

        idx = pos + 2
        elements = []

        for _ in range(num_elements):
            if idx >= len(self.buffer) or self.buffer[idx] != '$':
                return None, self.buffer

            pos_len = self.buffer.find('\r\n', idx)
            if pos_len == -1:
                return None, self.buffer

            try:
                str_len = int(self.buffer[idx+1:pos_len])
            except:
                raise ValueError("Invalid bulk string length")

            idx = pos_len + 2
            if idx + str_len > len(self.buffer):
                return None, self.buffer

            element = self.buffer[idx:idx+str_len]
            elements.append(element)
            idx += str_len

            if self.buffer[idx:idx+2] != '\r\n':
                raise ValueError("Expected CRLF after bulk string")
            idx += 2

        remaining = self.buffer[idx:]
        self.buffer = remaining
        return elements, remaining

class SimpleTCPServer:
    def __init__(self, host='localhost', port=6379):
        self.host = host
        self.port = port
        self.storage: Dict[str, str] = {}
        self.expire: Dict[str, float] = {}
        self.socket = None
        self.parser = RESPParser()

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        print(f"Server listening on {self.host}:{self.port}")

        while True:
            client_socket, addr = self.socket.accept()
            print(f"Connection from {addr}")
            try:
                self.handle_client(client_socket)
            except Exception as e:
                logging.error(f"Error: {e}")
            finally:
                client_socket.close()
                print(f"Connection closed for {addr}")

    def handle_client(self, client_socket):
        self.parser = RESPParser()
        while True:
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                break

            logging.debug(f"Received raw data: {repr(data)}")
            self.parser.feed(data)
            while True:
                parsed_command, _ = self.parser.parse()
                if parsed_command is None:
                    break

                logging.debug(f"Parsed command: {parsed_command}")
                response = self.process_command(parsed_command)
                encoded = self.encode_resp(response)
                client_socket.send(encoded)
                logging.debug(f"Sent response: {repr(encoded.decode('utf-8'))}")

    def is_expired(self, key: str) -> bool:
        if key in self.expire:
            if time.time() >= self.expire[key]:
                del self.storage[key]
                del self.expire[key]
                return True
        return False

    def process_command(self, cmd):
        if not cmd:
            return "ERROR: Empty"

        command = cmd[0].upper()

        if command == "SET":
            return self.handle_set(cmd[1:])
        elif command == "GET":
            return self.handle_get(cmd[1:])
        elif command == "EXPIRE":
            return self.handle_expire(cmd[1:])
        elif command == "BENCHMARK":
            return self.handle_benchmark(cmd[1:])
        else:
            return f"ERROR: Unknown command {cmd[0]}"

    def handle_set(self, args):
        if len(args) < 2:
            return "ERROR: SET requires key and value"
        self.storage[args[0]] = args[1]
        return "OK"

    def handle_get(self, args):
        if len(args) < 1:
            return "ERROR: GET requires key"
        key = args[0]
        if self.is_expired(key):
            return None
        return self.storage.get(key, None)

    def handle_expire(self, args):
        if len(args) != 2:
            return "ERROR: EXPIRE requires key and seconds"
        key, seconds = args[0], args[1]
        if key not in self.storage:
            return None
        try:
            ttl = int(seconds)
            self.expire[key] = time.time() + ttl
            return "OK"
        except:
            return "ERROR: Invalid seconds"

    def handle_benchmark(self, args):
        if len(args) != 1:
            return "ERROR: BENCHMARK requires count"
        try:
            count = int(args[0])
            for i in range(count):
                key = f"key{i}"
                val = f"value{i}"
                self.storage[key] = val
            return f"OK: {count} keys inserted"
        except:
            return "ERROR: Invalid count"

    def encode_resp(self, data):
        if data is None:
            return b"$-1\r\n"
        if isinstance(data, str):
            if data.startswith("ERROR:"):
                return f"-{data[6:]}\r\n".encode('utf-8')
            elif data == "OK" or data.startswith("OK:"):
                return f"+{data}\r\n".encode('utf-8')
            return f"${len(data)}\r\n{data}\r\n".encode('utf-8')
        return f"+{str(data)}\r\n".encode('utf-8')

if __name__ == "__main__":
    server = SimpleTCPServer()
    server.start()
