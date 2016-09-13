# coding:utf-8

import daemon
import socket


class SocketServer:

    def __init__(self, sock_host, sock_port, handler):
        self.sock_host = sock_host
        self.sock_port = sock_port
        self.handler = handler

        self.listen = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start_server(self):
        self.socket.bind((self.sock_host, self.sock_port))
        self.socket.listen(1)

        while self.listen:
            connection, address = self.socket.accept()
            req = connection.recv(1024)

            # 处理关闭请求
            if req == 'stop':
                res = 'Stoping Server'
                connection.send(res)
                connection.close()
                os.unlink(self.sock_file)
                exit(0)
            # 处理状态请求
            elif req == 'status':
                res = 'Server is running'
                connection.send(res)
            # 处理其他请求
            elif req != '':
                res = req
                connection.send(res)


    def send_request(self, request):

         = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            client_socket.connect((self.sock_address, self.sock_port))
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

if __name__ == '__main__':

    flush('---')
    output('waiting')
    ss = SocketServer()

    try:
        msg = sys.argv[1]
    except Exception as e:
        msg = 'start'

    if msg == 'start':
        with daemon.DaemonContext():
            ss.create_server()
            ss.handle_msg()
            output(e)
    else:
        print ss.send_msg2(msg)
