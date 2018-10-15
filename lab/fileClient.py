#! /usr/bin/env python3

# Echo client program
import socket, sys, re, os
sys.path.append("../lib")       # for params
from threading import Thread
import params


switchesVarDefaults = (
    (('-s', '--server'), 'server', "127.0.0.1:50001"),
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )

progname = "fileClient"
paramMap = params.parseParams(switchesVarDefaults)
server, usage  = paramMap["server"], paramMap["usage"]

if usage:
    params.usage()

try:
    serverHost, serverPort = re.split(":", server)
    serverPort = int(serverPort)
except:
    print("Can't parse server:port from '%s'" % server)
    sys.exit(1)

class ClientThread(Thread):
    def __init__(self, serverHost, serverPort, debug):
        Thread.__init__(self, daemon=False)
        self.serverHost, self.serverPort, self.debug = serverHost, serverPort, debug
        self.start()

    def run(self):
        s = None
        for res in socket.getaddrinfo(serverHost, serverPort, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                print("creating sock: af=%d, type=%d, proto=%d" % (af, socktype, proto))
                s = socket.socket(af, socktype, proto)
            except socket.error as msg:
                print(" error: %s" % msg)
                s = None
                continue
            try:
                print(" attempting to connect to %s" % repr(sa))
                s.connect(sa)
            except socket.error as msg:
                print(" error: %s" % msg)
                s.close()
                s = None
                continue
            break

        if s is None:
            print('could not open socket')
            sys.exit(1)

        file = ""
        # Check for File
        while not os.path.exists(file):
            file = input("Enter the name of the file you wish to send:")

        header = "PUT {}".format(file).encode()
        s.send(header)
        received_len = 0
        sent_len = len(header)
        try:
            while received_len < sent_len:
                data = s.recv(100).decode()
                if data[-3:] == "EOF":
                    #print("Something went wrong! Lost connection to server.")
                    s.close()
                    sys.exit(1)
                received_len += len(data)

            print('Sending file...\n...\n')
            with open(file, 'r') as file:
                for line in file:
                    s.send(line.encode())
                    received_len = 0
                    sent_len = len(line)
                    while received_len < sent_len:
                        data = s.recv(100).decode()
                        received_len += len(data)
            s.send("EOF".encode())
            s.shutdown(socket.SHUT_WR)      # no more output
            print('File has been successfully sent! Shutting down client connection now.')
            while 1:
                data = s.recv(100).decode()
                if data[-3:] == "EOF":
                    break
        except:
            print('Something went wrong! Client or Server connection lost. Try again later.')
            #s.close()
            sys.exit(1)
        s.close()
