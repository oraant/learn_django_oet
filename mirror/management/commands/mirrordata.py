# coding:utf-8

from django.core.management.base import BaseCommand, CommandParser
from mirror.libs.server import Server

# complete this with daemon and socket server.


class Command(BaseCommand):  # todo : chinese support

    help = "Start or stop mirroring data from Target Oracle Database."

    def __init__(self):
        BaseCommand.__init__(self)

        # try to get socket server.
        try:
            self.server = Server()
        except Exception as e:
            self.server = None
            self.init_error = str(e)

        # actions for arg parser.
        self.socket_server_actions = ['startup', 'shutdown', 'check']
        self.proxy_job_actions = ['start', 'stop', 'ping']

    def add_arguments(self, parser):
        """
        Add custom arguments for this command.
        Args:
            parser (CommandParser): parser arg from father function.
        """

        cmd = self  # make sure we can use sub parser in django. via stack_overflow

        class SubParser(CommandParser):
            """Use to avoid the error when using sub parser in django's add_arguments method."""
            def __init__(self, **kwargs):
                super(SubParser, self).__init__(cmd, **kwargs)

        # add custom sub commands.

        subparsers = parser.add_subparsers(
            title="sub commands",
            parser_class=SubParser,
            dest='sub_command',
            help='Sub commands you can use.'
        )

        # actions to start or stop socket server.

        server = subparsers.add_parser('server', help="Server Commands")
        server.add_argument(
            'action',
            metavar='ACTION',
            choices=self.socket_server_actions,
            help='Actions is: <%s>' % '|'.join(self.socket_server_actions),
        )

        # actions of targets when calling server is running.

        proxy = subparsers.add_parser('proxy', help="Proxy Commands")
        proxy.add_argument(
            '-a', '--action',
            metavar='ACTION',
            required=True,
            choices=self.proxy_job_actions,
            help='Actions is: <%s>' % '|'.join(self.proxy_job_actions)
        )
        proxy.add_argument(
            '-t', '--targets',
            metavar='TARGET',
            nargs='*',
            help='Targets can be empty which means ALL, you can list targets by <./manage.py mirrordata proxy -a ping>.'
        )

    def handle(self, *args, **options):
        """
        call different handle for different sub command.
        """
        if not self.server:
            print 'Error : %s' % self.init_error
            return

        handler_choice = {
            'proxy': self.proxy_handle,
            'server': self.server_handle,
        }

        sub_command = options['sub_command']
        handler_choice.get(sub_command)(options)

    def server_handle(self, options):

        functions = [self.server.startup, self.server.shutdown, self.server.check]
        operations = dict(zip(self.socket_server_actions, functions))

        action = options['action']
        print operations.get(action)()

    def proxy_handle(self, options):

        action = options['action']
        targets = options['targets']

        request = str({'action': action, 'targets': targets})
        print self.server.request(request)
