#!/usr/bin/env python3


import socket


HOST = "10.0.1.26"
PORT = 52015
MSG = 'Andreas'

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
s.connect((HOST, PORT))
s.send(MSG.encode())
data = s.recv(1024)
s.close()


