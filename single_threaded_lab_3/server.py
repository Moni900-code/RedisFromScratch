#!/usr/bin/env python3
"""
Single-threaded TCP Server with Redis-like command processing
Supports SET, GET commands with key expiration (EXPIRE) and RESP protocol
"""
import socket
import sys
import time
from typing import Dict, Optional, List, Tuple

class SimpleTCPServer:
    def __init__(self, host: str = 'localhost', port: int = 6379):
        self.host = host
        self.port = port
        self.storage: Dict[str, str] = {}
        self.expire: Dict[str, float] = {}  # key -> expire timestamp (epoch)
        self.socket = None
        
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
        """Handle client requests in a loop"""
        buffer = ""
        while True:
            try:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                while '\r\n' in buffer:
                    command, buffer = self.parse_resp(buffer)
                    if not command:
                        break
                    
                    print(f"Received RESP: {command}")
                    self.cleanup_expired_keys()
                    response = self.process_command(command)
                    client_socket.send(self.serialize_resp(response).encode('utf-8'))
                    print(f"Sent RESP: {response}")
                
            except ConnectionResetError:
                print("Client disconnected")
                break
            except Exception as e:
                error_response = f"-ERROR: {str(e)}\r\n"
                client_socket.send(error_response.encode('utf-8'))
                print(f"Error: {e}")

    def parse_resp(self, data: str) -> Tuple[Optional[List[str]], str]:
        """Parse RESP protocol data"""
        if not data.startswith('*'):
            return None, data
        
        lines = data.split('\r\n')
        if not lines:
            return None, data
        
        try:
            array_len = int(lines[0][1:])
            if array_len <= 0:
                return None, data
            
            command = []
            index = 1
            for _ in range(array_len):
                if index >= len(lines) or not lines[index].startswith('$'):
                    return None, data
                bulk_len = int(lines[index][1:])
                index += 1
                if index >= len(lines) or len(lines[index]) != bulk_len:
                    return None, data
                command.append(lines[index])
                index += 1
            
            remaining = '\r\n'.join(lines[index:]) if index < len(lines) else ""
            return command, remaining
        except ValueError:
            return None, data

    def serialize_resp(self, response: str) -> str :
        """Serialize response to RESP format"""
        if response.startswith('-'):
            return f"{response}\r\n"
        elif response == "(nil)":
            return "$-1\r\n"
        elif response == "OK":
            return "+OK\r\n"
        else:
            return f"${len(response)}\r\n{response}\r\n"

    def cleanup_expired_keys(self):
        """Remove expired keys"""
        now = time.time()
        expired_keys = [k for k, exp in self.expire.items() if exp <= now]
        for key in expired_keys:
            print(f"Key expired and removed: {key}")
            self.storage.pop(key, None)
            self.expire.pop(key, None)
    
    def process_command(self, command: list) -> str:
        """Process Redis-like commands"""
        if not command:
            return "-ERROR: Empty command"
        
        cmd = command[0].upper()
        
        if cmd == "SET":
            return self.handle_set(command[1:])
        elif cmd == "GET":
            return self.handle_get(command[1:])
        else:
            return f"-ERROR: Unknown command '{cmd}'"
    
    def handle_set(self, args: list) -> str:
        """Handle SET key value [EX seconds]"""
        if len(args) < 2:
            return "-ERROR: SET requires key and value"
        
        key = args[0]
        value = args[1]
        expire_time = None
        
        if len(args) > 2:
            i = 2
            while i < len(args):
                option = args[i].upper()
                if option == "EX":
                    i += 1
                    if i >= len(args):
                        return "-ERROR: EX requires a number"
                    try:
                        seconds = int(args[i])
                        if seconds <= 0:
                            return "-ERROR: EX seconds must be positive"
                        expire_time = time.time() + seconds
                    except ValueError:
                        return "-ERROR: EX requires an integer"
                else:
                    return f"-ERROR: Unknown option '{args[i]}'"
                i += 1
        
        self.storage[key] = value
        if expire_time is not None:
            self.expire[key] = expire_time
        elif key in self.expire:
            self.expire.pop(key)
        
        return "OK"
    
    def handle_get(self, args: list) -> str:
        """Handle GET key"""
        if len(args) < 1:
            return "-ERROR: GET requires key"
        
        key = args[0]
        
        if key in self.expire:
            if self.expire[key] <= time.time():
                self.storage.pop(key, None)
                self.expire.pop(key, None)
                return "(nil)"
        
        value = self.storage.get(key)
        return value if value is not None else "(nil)"
    
    def cleanup(self):
        """Clean up resources"""
        if self.socket:
            self.socket.close()

if __name__ == "__main__":
    server = SimpleTCPServer()
    server.start()