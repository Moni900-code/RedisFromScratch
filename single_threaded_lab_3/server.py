#!/usr/bin/env python3
"""
Simple single-threaded TCP server with RESP command parsing
Supports Redis-like SET and GET with optional EXPIRE
"""

import socket
import sys
import time
from typing import Dict, Optional

class RESPParser:
    """
    Simple RESP protocol parser for commands.
    Parses array of bulk strings like:
    *3\r\n$3\r\nSET\r\n$5\r\nmykey\r\n$5\r\nvalue\r\n
    """
    def __init__(self):
        self.buffer = ""

    def feed(self, data: str):
        self.buffer += data

    def parse(self):
        """
        Try to parse one full RESP command from buffer.
        Returns (command_list, remaining_buffer) or (None, buffer) if incomplete.
        """
        if not self.buffer:
            return None, self.buffer

        # RESP array must start with '*'
        if self.buffer[0] != '*':
            raise ValueError("Protocol error: expected '*' at start")

        # Find the first \r\n after '*'
        pos = self.buffer.find('\r\n')
        if pos == -1:
            return None, self.buffer  # incomplete

        # Number of elements in array
        try:
            num_elements = int(self.buffer[1:pos])
        except:
            raise ValueError("Protocol error: invalid array length")

        idx = pos + 2
        elements = []

        for _ in range(num_elements):
            if idx >= len(self.buffer):
                return None, self.buffer  # incomplete

            if self.buffer[idx] != '$':
                raise ValueError("Protocol error: expected '$'")

            # Find next \r\n for bulk string length
            pos_len = self.buffer.find('\r\n', idx)
            if pos_len == -1:
                return None, self.buffer  # incomplete

            try:
                str_len = int(self.buffer[idx+1:pos_len])
            except:
                raise ValueError("Protocol error: invalid bulk string length")

            idx = pos_len + 2
            # Now idx to idx+str_len is the string
            if idx + str_len > len(self.buffer):
                return None, self.buffer  # incomplete

            element = self.buffer[idx:idx+str_len]
            elements.append(element)
            idx += str_len

            # After string must be \r\n
            if self.buffer[idx:idx+2] != '\r\n':
                raise ValueError("Protocol error: expected CRLF after bulk string")
            idx += 2

        # parsed successfully
        remaining = self.buffer[idx:]
        self.buffer = remaining
        return elements, remaining

class SimpleTCPServer:
    def __init__(self, host: str = 'localhost', port: int = 6379):
        self.host = host
        self.port = port
        self.storage: Dict[str, str] = {}
        self.expire: Dict[str, float] = {}  # key -> expire timestamp (epoch)
        self.socket = None
        self.parser = RESPParser()

    def start(self):
        """Start the TCP server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            print(f"Server listening on {self.host}:{self.port}")
            print("Waiting for connections...")

            while True:
                client_socket, client_address = self.socket.accept()
                print(f"Connection from {client_address}")
                try:
                    self.handle_client(client_socket)
                except Exception as e:
                    print(f"Error handling client {client_address}: {e}")
                finally:
                    client_socket.close()
                    print(f"Connection closed for {client_address}")

        except KeyboardInterrupt:
            print("\nShutting down server...")
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.cleanup()

    def handle_client(self, client_socket: socket.socket):
        self.parser = RESPParser()  # reset parser for each client
        while True:
            try:
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                self.parser.feed(data)
                while True:
                    parsed_command, _ = self.parser.parse()
                    if parsed_command is None:
                        break  # incomplete, wait for more data

                    print(f"Received command: {parsed_command}")
                    self.cleanup_expired_keys()
                    response = self.process_command(parsed_command)
                    resp_bytes = self.encode_resp(response)
                    client_socket.send(resp_bytes)
                    print(f"Sent response: {response}")

            except ConnectionResetError:
                print("Client disconnected")
                break
            except Exception as e:
                err_msg = f"ERROR: {str(e)}"
                client_socket.send(self.encode_resp(err_msg))
                print(f"Error: {e}")
                break

    def cleanup_expired_keys(self):
        now = time.time()
        expired = [k for k, v in self.expire.items() if v <= now]
        for k in expired:
            print(f"Expired key removed: {k}")
            self.storage.pop(k, None)
            self.expire.pop(k, None)

    def process_command(self, parts):
        if not parts:
            return "ERROR: Empty command"

        cmd = parts[0].upper()
        if cmd == "SET":
            return self.handle_set(parts[1:])
        elif cmd == "GET":
            return self.handle_get(parts[1:])
        else:
            return f"ERROR: Unknown command '{cmd}'"

    def handle_set(self, args):
        if len(args) < 2:
            return "ERROR: SET requires key and value"

        key, value = args[0], args[1]
        expire_time = None
        idx = 2
        while idx < len(args):
            if args[idx].upper() == "EX":
                idx += 1
                if idx >= len(args):
                    return "ERROR: EX requires an argument"
                try:
                    seconds = int(args[idx])
                    if seconds <= 0:
                        return "ERROR: EX seconds must be positive"
                    expire_time = time.time() + seconds
                except:
                    return "ERROR: EX requires integer seconds"
            else:
                return f"ERROR: Unknown option '{args[idx]}'"
            idx += 1

        self.storage[key] = value
        if expire_time is not None:
            self.expire[key] = expire_time
        elif key in self.expire:
            self.expire.pop(key)

        return "OK"

    def handle_get(self, args):
        if len(args) < 1:
            return "ERROR: GET requires key"

        key = args[0]
        if key in self.expire and self.expire[key] <= time.time():
            self.storage.pop(key, None)
            self.expire.pop(key, None)
            return None  # nil

        return self.storage.get(key, None)

    def encode_resp(self, data):
        """
        Encode Python data into RESP reply:
        - None => $-1\r\n (nil)
        - str => bulk string: $len\r\nstring\r\n
        - "OK" => +OK\r\n
        - error string starting with "ERROR:" => -Error message\r\n
        """
        if data is None:
            return b"$-1\r\n"

        if isinstance(data, str):
            if data == "OK":
                return b"+OK\r\n"
            elif data.startswith("ERROR"):
                return f"-{data[6:]}\r\n".encode('utf-8')  # after "ERROR:"
            else:
                # bulk string
                return f"${len(data)}\r\n{data}\r\n".encode('utf-8')

        # fallback
        return f"+{str(data)}\r\n".encode('utf-8')

    def cleanup(self):
        if self.socket:
            self.socket.close()

if __name__ == "__main__":
    server = SimpleTCPServer()
    server.start()
