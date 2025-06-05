#!/usr/bin/env python3
"""
Multi-threaded TCP Server with Redis-like command processing
Handles multiple clients concurrently
"""

import socket
import sys
import threading
from typing import Dict, Optional

class SimpleTCPServer:
    def __init__(self, host: str = 'localhost', port: int = 6379):
        self.host = host
        self.port = port
        self.storage: Dict[str, str] = {}
        self.socket = None
        self.lock = threading.Lock()  # Lock for thread-safe storage access
        
    def start(self):
        """Start the TCP server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            print(f"Server listening on {self.host}:{self.port}")
            
            while True:
                client_socket, client_address = self.socket.accept()
                print(f"Connection from {client_address}")
                
                # Start a new thread for each client
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.start()
                
        except KeyboardInterrupt:
            print("\nShutting down server...")
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.cleanup()
    
    def handle_client(self, client_socket: socket.socket, client_address: tuple):
        """Handle client requests in a loop"""
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8').strip()
                if not data:
                    break
                
                print(f"Received from {client_address}: {data}")
                response = self.process_command(data)
                client_socket.send((response + '\n').encode('utf-8'))
                print(f"Sent to {client_address}: {response}")
                
        except ConnectionResetError:
            print(f"Client {client_address} disconnected")
        except Exception as e:
            error_response = f"ERROR: {str(e)}"
            client_socket.send((error_response + '\n').encode('utf-8'))
            print(f"Error for {client_address}: {e}")
        finally:
            client_socket.close()
            print(f"Connection closed for {client_address}")
    
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
        """Handle SET key value"""
        if len(args) < 2:
            return "ERROR: SET requires key and value"
        
        key = args[0]
        value = ' '.join(args[1:])
        with self.lock:  # Thread-safe storage access
            self.storage[key] = value
        return "OK"
    
    def handle_get(self, args: list) -> str:
        """Handle GET key"""
        if len(args) < 1:
            return "ERROR: GET requires key"
        
        key = args[0]
        with self.lock:  # Thread-safe storage access
            value = self.storage.get(key)
        return value if value is not None else "(nil)"
    
    def cleanup(self):
        """Clean up resources"""
        if self.socket:
            self.socket.close()

if __name__ == "__main__":
    server = SimpleTCPServer()
    server.start()