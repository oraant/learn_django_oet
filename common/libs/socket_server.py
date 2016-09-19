# coding:utf-8

import daemon
import socket
import functools


class SocketServer:

    def __init__(self, sock_host, sock_port, handler=None):
        self.sock_host = sock_host
        self.sock_port = sock_port
        self.handler = handler

        self.listen = True

        self.STATUS_SOCKET_SERVER, self.STOP_SOCKET_SERVER = 'STATUS_SOCKET_SERVER', 'STOP_SOCKET_SERVER'
        self.SERVER_IS_RUNNING, self.STOPPING_SERVER = 'SERVER_IS_RUNNING', 'STOPPING_SERVER'

    def start_server(self):
        print self.sock_host, self.sock_port
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.sock_host, self.sock_port))
        server_socket.listen(1)

        def status():
            connection.send(self.SERVER_IS_RUNNING)

        def stop():
            connection.send(self.STOPPING_SERVER)
            connection.close()
            self.listen = False

        actions = {
            self.STATUS_SOCKET_SERVER: status,
            self.STOP_SOCKET_SERVER: stop
        }

        while self.listen:
            connection, address = server_socket.accept()
            request = connection.recv(1024)
            print '===', request
            if request in actions.keys():
                actions.get(request)()
            elif self.handler:
                response = self.handler.handle(request)
                connection.send(response)
            else:
                connection.send("Server can't handle the request : %s" % request)

    def send_request(self, request):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((self.sock_host, self.sock_port))
            client_socket.send(request)
            response = client_socket.recv(1024)
        except socket.error as e:
            if e.errno == 111:
                response = str(e)
            else:
                raise e
        finally:
            client_socket.close()

        return response

    def status_server(self):
        return self.send_request(self.STATUS_SOCKET_SERVER)

    def stop_server(self):
        return self.send_request(self.STOP_SOCKET_SERVER)

    def test_server(self):
        response = self.send_request(self.STATUS_SOCKET_SERVER)
        if response == self.SERVER_IS_RUNNING:
            return True
        else:
            return False
