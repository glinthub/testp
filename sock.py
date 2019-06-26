import os
import sys
from socket import *

addr_client = "/tmp/socket_test_client"
addr_server = "/tmp/socket_test_server"

sock = socket(AF_UNIX, SOCK_DGRAM, 0)
if len(sys.argv) > 1 and sys.argv[1] == "c":
    if os.path.exists(addr_client):
        os.unlink(addr_client)
    sock.bind(addr_client)
    msg = "hello, greeting from python"
    print("sending: " + msg)
    msg = msg.encode("utf-8")
    sock.sendto(msg, addr_server)
    print("receiving...")
    msg,addr = sock.recvfrom(100)
    print("received: " + msg.decode())
else:
    if os.path.exists(addr_server):
        os.unlink(addr_server)
    sock.bind(addr_server)
    print("receiving...")
    while True:
        msg,addr = sock.recvfrom(100)
        print("received: " + msg.decode())
        msg = "hi, response from python"
        print("sending: " + msg)
        msg = msg.encode("utf-8")
        sock.sendto(msg, addr)
