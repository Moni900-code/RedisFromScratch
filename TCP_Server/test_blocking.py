#!/usr/bin/env python3
"""
Test script to demonstrate single-threaded blocking behavior
Creates multiple clients to show that server blocks on first connection
"""

import socket
import threading
import time
import sys

def create_client(client_id: int, delay: int = 0):
    """Create a client connection"""
    try:
        if delay:
            time.sleep(delay)
            
        print(f"[Client {client_id}] Attempting to connect...")
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 6379))
        
        print(f"[Client {client_id}] Connected! Sending commands...")
        
        # Send SET and GET commands
        commands = [
            f"SET client{client_id} hello{client_id}",
            f"GET client{client_id}"
        ]
        
        for cmd in commands:
            print(f"[Client {client_id}] Sending: {cmd}")
            client.send((cmd + '\n').encode('utf-8'))
            
            response = client.recv(1024).decode('utf-8').strip()
            print(f"[Client {client_id}] Received: {response}")
            
            time.sleep(1)  # Delay between commands to simulate blocking
        
        print(f"[Client {client_id}] Closing connection...")
        client.close()
        
    except Exception as e:
        print(f"[Client {client_id}] Error: {e}")

def test_blocking_behavior():
    """Test that demonstrates single-threaded blocking"""
    print("=== Testing Single-Threaded Blocking Behavior ===")
    
    # Create threads for multiple clients
    threads = []
    
    # Client 1 - connects immediately
    t1 = threading.Thread(target=create_client, args=(1, 0))
    threads.append(t1)
    
    # Client 2 - connects after 2 seconds
    t2 = threading.Thread(target=create_client, args=(2, 2))
    threads.append(t2)
    
    # Client 3 - connects after 3 seconds
    t3 = threading.Thread(target=create_client, args=(3, 3))
    threads.append(t3)
    
    # Count the number of clients
    client_count = len(threads)
    
    # Print dynamic message based on client count
    print(f"Starting {client_count} clients simultaneously...")
    print(f"Client 1 will connect first and hold the connection")
    if client_count > 1:
        print(f"Clients 2 to {client_count} will be blocked until Client 1 finishes")
    print()
    
    # Start all threads
    start_time = time.time()
    for t in threads:
        t.start()
    
    # Wait for all to complete
    for t in threads:
        t.join()
    
    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds")
    print("Notice: Clients are processed sequentially, not concurrently")

if __name__ == "__main__":
    print("Make sure the server is running before executing this test!")
    input("Press Enter to continue...")
    test_blocking_behavior()