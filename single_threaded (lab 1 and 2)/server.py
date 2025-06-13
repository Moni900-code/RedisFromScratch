#!/usr/bin/env python3
"""
Single-threaded TCP Server with Redis-like command processing
Supports SET and GET commands with key expiration (EXPIRE)
"""

import socket
import sys
import time
from typing import Dict, Optional

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
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind and listen
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)  # Single connection at a time
            
            print(f"Server listening on {self.host}:{self.port}")
            print("Waiting for connections...")
            
            while True:
                # Accept connection (blocks here for single-threaded behavior)
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
        while True:
            try:
                # Receive data
                data = client_socket.recv(1024).decode('utf-8').strip()
                if not data:
                    break
                
                print(f"Received: {data}")
                
                # Cleanup expired keys on every command
                self.cleanup_expired_keys()
                
                # Process command
                response = self.process_command(data)
                
                # Send response
                client_socket.send((response + '\n').encode('utf-8'))
                print(f"Sent: {response}")
                
            except ConnectionResetError:
                print("Client disconnected")
                break
            except Exception as e:
                error_response = f"ERROR: {str(e)}"
                client_socket.send((error_response + '\n').encode('utf-8'))
                print(f"Error: {e}")

    def cleanup_expired_keys(self):
        """Remove expired keys"""
        now = time.time()
        expired_keys = [k for k, exp in self.expire.items() if exp <= now]
        for key in expired_keys:
            print(f"Key expired and removed: {key}")
            self.storage.pop(key, None)
            self.expire.pop(key, None)
    
    def process_command(self, command: str) -> str:
        """Process Redis-like commands"""
        parts = command.split()
        if not parts:
            return "ERROR: Empty command"
        
        cmd = parts[0].upper()
        
        if cmd == "SET":
            return self.handle_set(parts[1:])
        elif cmd == "GET":
            return self.handle_get(parts[1:])
        else:
            return f"ERROR: Unknown command '{cmd}'"
    
    def handle_set(self, args: list) -> str:
        """Handle SET key value [EX seconds]"""
        if len(args) < 2:
            return "ERROR: SET requires key and value"
        
        key = args[0]
        value = args[1]
        
        # Default expire = None
        expire_time = None
        
        # Check for optional EX param: e.g. SET key value EX 10
        if len(args) > 2:
            i = 2
            while i < len(args):
                option = args[i].upper()
                if option == "EX":
                    i += 1
                    if i >= len(args):
                        return "ERROR: EX requires a number"
                    try:
                        seconds = int(args[i])
                        if seconds <= 0:
                            return "ERROR: EX seconds must be positive"
                        expire_time = time.time() + seconds
                    except ValueError:
                        return "ERROR: EX requires an integer"
                else:
                    return f"ERROR: Unknown option '{args[i]}'"
                i += 1
        
        self.storage[key] = value
        if expire_time is not None:
            self.expire[key] = expire_time
        elif key in self.expire:
            # Remove expiration if no EX provided
            self.expire.pop(key)
        
        return "OK"
    
    def handle_get(self, args: list) -> str:
        """Handle GET key"""
        if len(args) < 1:
            return "ERROR: GET requires key"
        
        key = args[0]
        
        # Check expiration first
        if key in self.expire:
            if self.expire[key] <= time.time():
                # Key expired, delete it
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