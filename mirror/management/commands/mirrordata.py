# coding:utf-8

from django.core.management.base import BaseCommand, CommandParser
import daemon
from mirror.models import GlobalConfig, OracleTarget
from mirror.libs.handler import Handler
from common.libs.socket_server import SocketServer

# complete this with daemon and socket server.


class Command(BaseCommand):

    help = "Start or stop mirroring data from Target Oracle Database. "

    def __init__(self):
        BaseCommand.__init__(self)

        # get socket server object.
        self.config = GlobalConfig.objects.get(enable=True)
        self.handler = Handler()
        self.server = SocketServer(self.config.sock_addr, self.config.sock_port, self.handler)

        # actions for arg parser.
        self.socket_server_actions = ['startup', 'shutdown', 'check']
        self.proxy_process_actions = ['open', 'close']
        self.proxy_job_actions = ['start', 'stop', 'status', 'restart', 'reborn']

        # target names can be choice.
        self.targets = [x.name for x in OracleTarget.objects.all()]

    def add_arguments(self, parser):
        """
        Args:
            parser (CommandParser): parser arg from father function.
        """

        # make sure we can use sub parser in django. via stack_overflow

        cmd = self

        class SubParser(CommandParser):

            def __init__(self, **kwargs):
                super(SubParser, self).__init__(cmd, **kwargs)

        # do the main job

        subparsers = parser.add_subparsers(
            title="sub commands",
            parser_class=SubParser,
            dest='sub_command',
            help='Sub commands you can use.'
        )

        server = subparsers.add_parser('server', help="Server Commands")
        server.add_argument(
            'action',
            metavar='ACTION',
            choices=self.socket_server_actions,
            help='Actions is: <%s>' % '|'.join(self.socket_server_actions),
        )

        proxy = subparsers.add_parser('proxy', help="Proxy Commands")
        proxy.add_argument(
            '-a', '--action',
            metavar='ACTION',
            required=True,
            choices=self.proxy_job_actions + self.proxy_process_actions,
            help='Actions is: <%s>' % '|'.join(self.proxy_job_actions + self.proxy_process_actions),
        )
        proxy.add_argument(
            '-t', '--targets',
            metavar='TARGET',
            nargs='+',
            choices=self.targets,
            default=self.targets,
            help='Targets can be empty or some of [%s]' % '|'.join(self.targets)
        )

    def handle(self, *args, **options):
        """
        send user args to server, or start server.
        """

        handler_choice = {
            'proxy': self.proxy_handle,
            'server': self.server_handle,
        }

        sub_command = options['sub_command']
        handler_choice.get(sub_command)(options)

    def server_handle(self, options):
        action = options['action']

        def startup():
            if not self.server.test_server():
                with daemon.DaemonContext():
                    self.server.start_server()
                self.server.start_server()
            else:
                msg = self.server.status_server()
                self.stdout.write(msg)

        def shutdown():
            if self.server.test_server():
                msg = self.server.stop_server()
            else:
                msg = self.server.status_server()
            self.stdout.write(msg)

        def check():
            msg = self.server.status_server()
            self.stdout.write(msg)

        functions = [startup, shutdown, check]
        operations = dict(zip(self.socket_server_actions, functions))
        operations.get(action)()

    def proxy_handle(self, options):

        if not self.server.test_server():
            self.stdout.write('Server is not running, Please start it first.')
            return

        action = options['action']
        targets = options['targets']

        request = str(
            {'action': action, 'targets': targets}
        )

        print self.server.send_request(request)
