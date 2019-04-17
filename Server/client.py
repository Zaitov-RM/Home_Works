#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket,time

sock = socket.socket()
sock.connect(('127.0.0.1', 9090))



t=str(input())
sock.send(t.encode("utf-8"))
#prit(sock.recv(1024).decode("utf-8"))
data = sock.recv(1024)
sock.close()

print (data.decode("utf-8"))
time.sleep(5)

