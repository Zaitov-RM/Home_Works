#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket

print("Server started ")
sock = socket.socket()
sock.bind(('', 9090))
sock.listen(1)
conn, addr = sock.accept()

print ('connected:', addr)
#conn.send("Вы подключились к серверу".encode("utf-8"))

while True:
    data = conn.recv(1024)
    if not data:
        break
    print(data.decode("utf-8"))  
    conn.send(data.upper())
conn.close()
