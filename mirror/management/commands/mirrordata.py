# coding:utf-8

from django.core.management.base import BaseCommand, CommandError
from mirror.libs.proxy import Proxy
from argparse import ArgumentParser
import daemon
import multiprocessing as multi
from mirror.models import GlobalConfig, OracleTarget
import socket
import os,sys,time
import logging,warnings

# complete this with daemon and socket server.

class Command(BaseCommand):

#    def call(self,dbconfig):
#        try:
#            proxy = Proxy(dbconfig)
#            process = multi.Process(target=proxy.schedule())
#            process.start()
#        except Exception,e:
#            print "===",Exception,e
#            return
#
#    def handle(self, *args, **options):
#        logging.basicConfig()
#        warnings.filterwarnings("ignore")
#
#        from puller.models import DBConfigs
#        dbconfigs=DBConfigs.objects.all()
#        map(self.call,dbconfigs)
#        print '=== handle done'

    help = "Start or stop mirroring data from Target Oracle Database. "

    def __init__(self):
        BaseCommand.__init__(self)
        self.config = GlobalConfig.objects.get(enable=True)
        self.handler = Handler()
        self.server = SocketServer(self.config.sock_addr, self.config.sock_port, self.handler)

    def add_arguments(self, parser):
        """
        Args:
            parser (argparser.ArgumentParser):

        """
        actions = ['startup', 'shutdown', 'ping', 'open', 'close', 'start', 'stop', 'status', 'restart', 'reborn']
        parser.add_argument(
            '-a', '--action',
            choices=actions,
            required=True,
            help='Actions is: <%s>' % '|'.join(actions)
        )

        targets = [x.name for x in OracleTarget.objects.all()]
        parser.add_argument(
            '-t', '--targets',
            nargs='*',
            choices=targets,
            default=targets,
            help='Targets can be empty or some of [%s]' % '|'.join(targets)
        )

    def handle(self, *args, **options):
        """
        send user args to server, or start server.
        """

        action = options["action"]
        targets = options["targets"]

        if not targets:
            self.stdout.write("Syntax Error: No targets found. Try -h option.")
            return

        request = "-a %s -t %s" % (action, ' '.join(targets))

        if self.server.test_server():
            print 'sending'
            print self.server.send_request(request)
        else:
            print 'opening'
            with daemon.DaemonContext():
                self.server.start_server()


class SocketServer:

    ping, pong = "PING", "PONG"

    def __init__(self, sock_address, sock_port, handler):
        self.parser = self.__create_parser()
        self.listen = True

        self.sock_address = sock_address
        self.sock_port = sock_port
        self.handler = handler

    # parse options

    @staticmethod
    def __create_parser():
        parser = ArgumentParser()
        parser.add_argument('-a', '--action', required=True)
        parser.add_argument('-t', '--targets', nargs='*')
        return parser

    def get_options(self, args):
        return self.parser.parse_args(args.split())

    # talk to server

    def test_server(self):
        response = self.send_request(self.ping)
        if response == self.pong:
            return True
        else:
            return False

    def send_request(self, request):

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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

    # start server and keep listening

    def start_server(self):

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.sock_address, self.sock_port))
        server_socket.listen(1)

        while self.listen:
            conn, address = server_socket.accept()
            request = conn.recv(1024)
            options = self.get_options(request)
            response = self.request_handler(options)
            return response

    # do the main job.

    def request_handler(self, options):

        def close():
            self.listen = False
            return

        def ping():
            return "PONG"

        operations = {
            "ping": ping,
            "close": close,
        }

        action = options["action"]
        if action in operations.keys():
            response = operations.get(action)()
        else:
            response = self.handler.handle(options)

        return response  # todo : ...


class Handler:

    def __init__(self):
        pass

    def handle(self, options):
        return options