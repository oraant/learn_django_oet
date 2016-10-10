from mirror.libs.proxy import Proxy
from mirror.models import GlobalConfig, OracleTarget
from common.libs.socket_server import SocketServer
from cloghandler import ConcurrentRotatingFileHandler as LogHandler  # won't use this
# from logging.handlers import RotatingFileHandler as LogHandler
import logging
import os
from django.conf import settings


class Server(SocketServer):

    def __init__(self, sock_host, sock_port):

        self.config = GlobalConfig.objects.get(enable=True)
        SocketServer.__init__(self, self.config.sock_addr, self.config.sock_port)

        self.set_logger()

        self.proxies = dict()

        for target in OracleTarget.objects.all():
            name = target.name
            proxy = Proxy(target, self.logger)
            self.proxies.update(name=proxy)

    def set_logger(self):
        """
        Add handler for father's logger, and set it's log level.
        """

        log_file = os.path.abspath(self.config.log_file)
        log_level = self.config.log_level
        log_size = self.config.log_size * 1024 * 1024
        log_count = self.config.log_count
        log_format = self.config.log_format

        try:  # get log_file
            log_handler = LogHandler(log_file, 'a', log_size, log_count)
        except IOError:
            log_file = os.path.join(settings.BASE_DIR, 'data', 'mirror.log')
            log_handler = LogHandler(log_file, 'a', log_size, log_count)

        formatter = logging.Formatter(log_format)
        log_handler.setFormatter(formatter)

        self.logger.name = "MirrorData"
        self.logger.addHandler(log_handler)
        self.logger.setLevel(log_level)

        self.context.files_preserve = [log_handler.stream]  # make sure logger can be used in daemon process.
        self.logger.debug("set logger done")

    def _handle(self, request):
        """
        Args:
            request (str):

        Returns:
            response (str): response for request.
        """
        self.logger.debug("handling request: %s" % request)

        options = eval(request)
        action = options['action']
        targets = options['targets']

        responses = []

        for name in targets:
            proxy = self.proxies.get(name)
            response = self.call(proxy, action)
            responses.append(response)

        return '\n'.join(responses)

    @staticmethod
    def call(proxy, function):
        """

        Args:
            proxy (Proxy):
            function (str):

        Returns:

        """

        operations = {
            "open": proxy.open,
            "close": proxy.close,
            "start": proxy.start,
            "stop": proxy.stop,
            "restart": proxy.restart,
            "reborn": proxy.reborn,
            "check": proxy.check,
        }

        return operations.get(function)()
