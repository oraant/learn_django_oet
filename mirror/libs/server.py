from mirror.libs.proxy import Proxy
from common.libs.socket_server import SocketServer
# from cloghandler import ConcurrentRotatingFileHandler as LogHandler  # won't use this
from logging.handlers import RotatingFileHandler as LogHandler
import logging
import os
from django.conf import settings


class Server(SocketServer):
    """
    Receive request from user, and manage proxy for every oracle target.
    Attributes:
        proxies (dict{str:Proxy}): a dict contains all proxy for every target.
    """

    def __init__(self, global_config, oracle_targets):
        """
        Init socket server, overwrite it's logger and context, and prepare proxy for every oracle target.
        Args:
            global_config (mirror.models.GlobalConfig): global configs
            oracle_targets (list[mirror.models.OracleTarget]): oracle targets
        """

        # init parent class's instance.
        SocketServer.__init__(self, global_config.sock_addr, global_config.sock_port)

        # get proxies for every oracle target.  # todo : should be in _start() method, but oracle target will error.
        self.proxies = [(target.name, Proxy(target, self.logger)) for target in oracle_targets]
        self.proxies = dict(self.proxies)

        # list of opened and started proxy  # todo : should have reborn
        self.opened_proxies = set()
        self.started_proxies = set()

        # overwrite father class's logger and daemon context
        self.__set_logger(global_config)
        self.__set_context()

    def __set_logger(self, config):  # todo : processes's number better less than 50
        """
        Overwrite father's logger: add handler, set log level and format.
        Args:
            config (mirror.models.GlobalConfig): global configs
        """

        # get log configs
        log_file = os.path.abspath(config.log_file)
        log_level = config.log_level
        log_size = config.log_size * 1024 * 1024
        log_count = config.log_count
        log_format = config.log_format

        # get log_file
        try:
            log_handler = LogHandler(log_file, 'a', log_size, log_count)
        except IOError:
            log_file = os.path.join(settings.BASE_DIR, 'data', 'mirror.log')
            log_handler = LogHandler(log_file, 'a', log_size, log_count)

        # set format
        formatter = logging.Formatter(log_format)
        log_handler.setFormatter(formatter)

        # custom logger
        self.logger.name = "MirrorData"
        self.logger.addHandler(log_handler)
        self.logger.setLevel(log_level)

        # write first log!
        self.logger.debug("============================================================")
        self.logger.debug("set logger done.")

    def __set_context(self):
        """custom parent's daemon context, make sure Pipe and Logger in child can work."""
        self.logger.debug("custom parent's daemon context.")

        # get file descriptors for logger and Pipe connections in every proxy.
        preserves = [handler.stream for handler in self.logger.handlers]
        for proxy in self.proxies.values():
            preserves += proxy.filenos

        self.context.files_preserve = preserves  # make sure logger can be used in daemon process.

    def _handle(self, request):
        """
        Handle request and return response.
        Args:
            request (str): user's request
        Returns:
            response (str): response for request.
        """
        self.logger.debug("handling request: %s" % request)

        options = eval(request)
        action = options['action']
        targets = options['targets']

        response = [self.__call(target, action) for target in targets]
        return response

    def __call(self, target, function):
        """
        Call proxy's function and get response.
        Args:
            target (str): name of proxy
            function (str): which function to call
        Returns:
            str: response
        """

        self.logger.debug("calling %s's %s" % (target, function))

        proxy = self.proxies.get(target)

        # let server know the proxies's status
        if function == "open":
            self.opened_proxies.add(target)
        elif function == "close":
            self.opened_proxies.remove(target)
        elif function == "start":
            self.started_proxies.add(target)
        elif function == "stop":
            self.started_proxies.remove(target)

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

    def _stop(self):
        for target in self.started_proxies:
            self.__call(target, "stop")

        for target in self.opened_proxies:
            self.__call(target, "close")