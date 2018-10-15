#! /usr/bin/env python3

import socket, sys, re, os
from threading import Thread
import time
sys.path.append("../lib")
import params

current_dir = os.getcwd() + '/server/'
if not os.path.exists(current_dir):
    os.makedirs(current_dir)

switchesVarDefaults = (
        (('-l', '--listenPort') ,'listenPort', 50001),
        (('-?', '--usage'), "usage", False), # boolean (set if present)
    )

paramMap = params.parseParams(switchesVarDefaults)
listenPort = paramMap['listenPort']
listenAddr = ''

debug, listenPort = paramMap['debug'], paramMap['listenPort']

if paramMap['usage']:
    params.usage()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((listenAddr, listenPort))
server.listen(2)
print('Server now listening on port: {}'.format(listenPort))

class ServerThread(Thread):
    requestCount = 0
    def __init__(self, conn, addr, lock, debug):
        Thread.__init__(self, daemon=True)
        self.conn = conn
        self.addr = addr
        self.debug = debug
        self.lock = lock
        self.start()
    
    def run(self):
        output_file = None
        while True:
            print('Connection established with: {}'.format(self.addr))
            header = {
                "type": "",
                "url": ""
            }
            try:
                while True:
                    with self.lock:
                        data = self.conn.recv(100).decode()
                        if data == "":
                            continue
                        if data == "EOF":
                            self.conn.send("File read. Closing connection. EOF".encode())
                            output_file.close()
                            print('File read. Connection with: {} has now been closed'.format(addr))
                            self.conn.close()
                            break
                        if data.startswith('PUT'):
                            data_copy = data
                            data = data.split()
                            header['type'] = data[0]
                            header['url'] = current_dir + data[1]
                            if not os.path.exists(header['url']):
                                open(header['url'], 'w+').close()
                                output_file = open(header['url'], 'a')
                            else:
                                output_file = open(header['url'], 'w+')
                            self.conn.send(data_copy.encode())
                        else:
                            if header['type'] == "PUT":
                                output_file.write(data)
                            self.conn.send(data.encode())
            except:
                print('Something went wrong! Connection with client has been lost.')
                self.conn.send("EOF".encode())
                self.conn.close()
                sys.exit(1)
                break
            requestNum = ServerThread.requestCount
            time.sleep(0.001)
            ServerThread.requestCount = requestNum + 1
        #msg = ("%s! (%d)" % (msg, requestNum)).encode()
        #self.fsock.sendmsg(msg)

lock = threading.Lock()
while True:
    sock, addr = server.accept()
    ServerThread(sock, addr, lock, debug)
