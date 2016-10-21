from mirror.libs.proxy import Proxy
from common.libs.socket_server import SocketServer
from common.libs.job_manager import JobManager
from logging.handlers import RotatingFileHandler as LogHandler
import logging
import os
from django.conf import settings
from mirror.models import OracleTarget
from django.db import connection


class Server(SocketServer):
    """
    Receive request from user, and manage proxy for every oracle target.
    Attributes:
        proxy_managers (dict{str:JobManager}): a dict contains all proxy for every target.
        check_time (int):
        logger_name (str):
    """

    # initial codes

    def __init__(self, global_config):  # todo : config and oracle targets, receive or import by it self.
        """
        Init socket server, overwrite it's logger and context, and prepare proxy for every oracle target.
        Args:
            global_config (mirror.models.GlobalConfig): global configs
        """

        # init parent class's instance.
        SocketServer.__init__(self, global_config.sock_addr, global_config.sock_port)

        # overwrite father class's logger and daemon context
        self.logger_name = 'Mirror'
        self.__set_logger(global_config)
        self.__set_context()

        # global variables
        self.proxy_managers = {}
        self.check_time = global_config.reborn.seconds

        # todo : concurrent process config

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
        self.logger.name = self.logger_name
        self.logger.addHandler(log_handler)
        self.logger.setLevel(log_level)

        # write first log!
        self.logger.debug("="*30)
        self.logger.debug("set logger done.")

    def __set_context(self):
        """custom parent's daemon context, make sure Pipe and Logger in child can work."""
        self.logger.debug("custom parent's daemon context.")

        # get file descriptors for logger and Pipe connections in every proxy.
        preserves = [handler.stream for handler in self.logger.handlers]

        self.context.files_preserve = preserves  # make sure logger can be used in daemon process.

    # overwrite parent's method.

    def _startup(self):  # todo : handle exception.
        """Init proxies for every oracle target when startup server."""
        connection.close()
        oracle_targets = OracleTarget.objects.all()
        target_names = [target.name for target in oracle_targets]

        for target_name in target_names:
            child_logger_name = self.logger_name + '.<%s>' % target_name
            proxy = Proxy(target_name, child_logger_name)
            proxy_manager = JobManager(proxy, child_logger_name, self.check_time)
            self.proxy_managers[target_name] = proxy_manager

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

        response = []
        for target in targets:
            proxy_manager = self.proxy_managers.get(target)
            result, msg = proxy_manager.call(action)
            response.append('Target <%s>: [%s] - %s' % (target, result, msg))

        return '\n'.join(response)

    def _shutdown(self):
        """
        Stop and close all proxies before shutdown.
        """
        for proxy_manager in self.proxy_managers.values():
            proxy_manager.stop()
