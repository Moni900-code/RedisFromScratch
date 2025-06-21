import socket
import time

for i in range(300):
    s = socket.socket()
    s.connect(('localhost', 6379))
    s.send(b'*5\r\n$3\r\nSET\r\n$4\r\nkey\r\n$5\r\nvalue\r\n$2\r\nEX\r\n$1\r\n2\r\n')
    s.recv(1024)
    time.sleep(0.01)
    s.send(b'*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n')
    s.recv(1024)
    s.close()
    time.sleep(0.01)
