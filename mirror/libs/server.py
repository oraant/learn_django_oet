from mirror.libs.proxy import Proxy
from mirror.models import GlobalConfig, OracleTarget
from common.libs.socket_server import SocketServer
# from cloghandler import ConcurrentRotatingFileHandler as LogHandler  # won't use this
from logging.handlers import RotatingFileHandler as LogHandler  # todo : processes's number better less than 50
import logging
import os
from django.conf import settings


class Server(SocketServer):

    def __init__(self):

        # init parent class's instance.
        self.config = GlobalConfig.objects.get(enable=True)
        SocketServer.__init__(self, self.config.sock_addr, self.config.sock_port)

        # get proxies for every oracle target.
        self.proxies = dict()
        for target in OracleTarget.objects.all():
            name = target.name
            proxy = Proxy(target, self.logger)
            self.proxies[name] = proxy

        # overwrite parent's logger and context, to make sure Pipe and Logger in child can work.
        self.set_logger()
        self.set_context()

        self.logger.debug("proxies is: %s" % str(self.proxies))

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

    def set_context(self):
        """custom parent's daemon context."""

        # get file descriptors for logger and Pipe connections in every proxy.
        preserves = [handler.stream for handler in self.logger.handlers]
        for proxy in self.proxies.values():
            preserves += proxy.filenos

        self.context.files_preserve = preserves  # make sure logger can be used in daemon process.
        self.logger.debug("==== --- set logger done --- ====")
        self.logger.debug("tttt %s " % str(preserves))

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

        self.logger.debug("handled options is: %s" % str(options))
        response_list = []
        for name in targets:
            self.logger.debug("name is: %s" % name)
            proxy = self.proxies.get(name)
            self.logger.debug("proxy is: %s" % str(proxy))
            proxy_response = self.call(proxy, action)
            response_list.append(proxy_response)
        response = '\n'.join(response_list)

        self.logger.debug("response is : %s" % response)
        return response

    def call(self, proxy, function):
        """
        Args:
            proxy (Proxy):
            function (str):

        Returns:
            str: response
        """

        self.logger.debug("calling %s's %s" % (proxy.target.name, function))

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
