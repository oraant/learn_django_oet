from mirror.libs.proxy import Proxy
from common.libs.socket_server import SocketServer
from common.libs.job_manager import JobManager
from logging.handlers import RotatingFileHandler as LogHandler
import logging
import os
from django.conf import settings
from mirror.models import GlobalConfig, OracleTarget
from django.db import connection


class Server(SocketServer):
    """
    Receive request from user, and manage proxy for every oracle target.
    Attributes:
        proxy_managers (dict{str:JobManager}): a dict contains all proxy_managers for every target.
        check_time (int): period for proxy_managers to check job's healthy, unit is seconds.
        logger_name (str): name of this model's logger.
    """

    # initial codes

    def __init__(self):  # todo : config and oracle targets, receive or import by it self.
        """
        Init socket server, overwrite it's logger and context, and prepare proxy for every oracle target.

        Raises:
            django.db.utils.OperationalError: can't connect to mysql server
            IndexError: doesn't have enabled global configuration.
        """

        # get configs from model.
        self.global_config = GlobalConfig.objects.filter(enable=True)[0]
        self.oracle_targets = OracleTarget.objects.all()

        # init parent class's instance.
        SocketServer.__init__(self, self.global_config.sock_addr, self.global_config.sock_port)

        # global variables
        self.logger_name = 'Mirror'
        self.proxy_managers = {}
        self.check_time = self.global_config.reborn.seconds

        # overwrite father class's logger and daemon context
        self.__set_logger()
        self.__set_context()

    def __set_logger(self):  # todo : processes's number better less than 50
        """
        Overwrite father's logger: add handler, set log level and format.
        """

        # get log configs
        log_file = os.path.abspath(self.global_config.log_file)
        log_size = self.global_config.log_size * 1024 * 1024
        log_count = self.global_config.log_count
        log_level = self.global_config.log_level
        log_format = self.global_config.log_format

        # get log_file
        error_msg = ''
        try:
            log_handler = LogHandler(log_file, 'a', log_size, log_count)
        except IOError as e:
            default_log_file = os.path.join(settings.BASE_DIR, 'data', 'mirror.log')
            log_handler = LogHandler(default_log_file, 'a', log_size, log_count)
            error_msg = "log_file %s is not usable by (%s), change it to %s" % (log_file, e, default_log_file)

        # set format
        formatter = logging.Formatter(log_format)
        log_handler.setFormatter(formatter)

        # custom logger
        self.logger.name = self.logger_name
        self.logger.addHandler(log_handler)
        self.logger.setLevel(log_level)

        # write first log if have error.
        if error_msg:
            self.logger.error(error_msg)

    def __set_context(self):
        """custom parent's daemon context, make sure Pipe and Logger in child can work."""
        self.logger.debug("custom parent's daemon context.")

        # get file descriptors for logger
        preserves = [handler.stream for handler in self.logger.handlers]

        self.context.files_preserve = preserves  # make sure logger can be used in daemon process.

    # overwrite parent's method.

    def _startup(self):  # todo : handle exception.
        """
        Init proxies for every oracle target when startup server.
        Raises:
            django.db.utils.OperationalError:
        Returns:
            bool: startup successful or not.
        """

        connection.close()  # make sure models can be use after process run in daemon.

        target_names = [target.name for target in self.oracle_targets]

        for target_name in target_names:
            child_logger_name = self.logger_name + '.<%s>' % target_name
            proxy = Proxy(target_name, child_logger_name)
            proxy_manager = JobManager(proxy, child_logger_name, self.check_time)
            self.proxy_managers[target_name] = proxy_manager

        return True, 'startup done.'

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

        if not targets:
            targets = [x.name for x in self.oracle_targets.all()]

        response = []
        for target in targets:
            proxy_manager = self.proxy_managers.get(target)
            result, msg = proxy_manager.call(action)
            response.append('%20s - [%5s] - %s' % (target, result, msg))

        self.logger.debug("get response of %s" % response)
        return '\n'.join(response)

    def _shutdown(self):
        """
        Try to stop and close all proxies before shutdown.
        Returns:
            str: messages of shutdown results
        """
        response = []
        for target in self.proxy_managers:
            result, msg = self.proxy_managers[target].stop()
            response.append('%20s - [%5s] - %s' % (target, result, msg))
        response.append('%18s %s' % ('', 'Server Stopped.'))

        return True, '\n'.join(response)
