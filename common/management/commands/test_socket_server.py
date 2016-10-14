# coding:utf-8

from django.core.management.base import BaseCommand, CommandParser
from common.libs.socket_server import SocketServer


class MySocketServer(SocketServer):

    hello_request = "hello"
    joe_request = "joe"
    test_request = "test"

    hello_response = "Hello World~"
    joe_response = "Joe is handsome~"
    test_response = "Test successful~"

    def _handle(self, request):

        responses = {
            self.hello_request: self.hello_response,
            self.joe_request: self.joe_response,
            self.test_request: self.test_response
        }

        if request in responses.keys():
            return responses.get(request)
        else:
            return 'Sorry, I don\'t know what you are talking about.'


class Command(BaseCommand):

    """
    This command is for Django's Test Case in common.tests.test_socket_server.py
    """

    help = "Start or stop mirroring data from Target Oracle Database. "

    def __init__(self):
        BaseCommand.__init__(self)

        # get socket server object.
        sock_addr = '127.0.0.1'
        sock_port = 15520
        self.myss = MySocketServer(sock_addr, sock_port)

        # actions for arg parser.

    def add_arguments(self, parser):
        """
        Add custom arguments for this command.
        Args:
            parser (CommandParser): parser arg from father function.
        """

        parser.add_argument(
            'actions',
            nargs='*',
            metavar='ACTION',
        )

    def handle(self, *args, **options):
        """
        call command with string function and args.
        """

        functions = {
            'start': self.myss.startup,
            'request': self.myss.request,
            'stop': self.myss.shutdown,
            'check': self.myss.check,
            'test': self.myss.ping
        }

        actions = options['actions']
        function = actions[0]
        try:
            parameter = actions[1]
        except:
            parameter = None

        if not function:
            self.stdout.write('no action\'s here')

        if function not in functions.keys():
            self.stdout.write('unknown command')

        if parameter:
            result = functions.get(function)(parameter)
        else:
            result = functions.get(function)()

        self.stdout.write(str(result))
