#!/usr/bin/env python3
"""
TCP Client for connecting to the SimpleTCPServer
Supports interactive mode and single command mode
"""

import socket
import sys

class SimpleTCPClient:
    def __init__(self, host: str = 'localhost', port: int = 6379):
        self.host = host
        self.port = port
        self.socket = None
        
    def connect(self) -> bool:
        """Connect to the server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def send_command(self, command: str) -> str:
        """Send command and receive response"""
        try:
            # Send command
            self.socket.send((command + '\n').encode('utf-8'))
            
            # Receive response
            response = self.socket.recv(1024).decode('utf-8').strip()
            return response
        except Exception as e:
            return f"ERROR: {e}"
    
    def interactive_mode(self):
        """Run in interactive mode"""
        print("Interactive mode. Type 'quit' or 'exit' to exit.")
        print("Supported commands: SET key value [EX seconds], GET key")
        
        while True:
            try:
                command = input(f"{self.host}:{self.port}> ").strip()
                if not command:
                    continue
                
                if command.lower() in ('exit', 'quit'):
                    break
                
                response = self.send_command(command)
                print(response)
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except EOFError:
                print("\nExiting...")
                break
    
    def close(self):
        """Close connection"""
        if self.socket:
            self.socket.close()

def main():
    client = SimpleTCPClient()
    
    if not client.connect():
        sys.exit(1)
    
    try:
        client.interactive_mode()
    finally:
        client.close()

if __name__ == "__main__":
    main()
