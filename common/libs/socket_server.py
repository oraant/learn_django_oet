from daemon import DaemonContext
import socket
import logging
import traceback


class SocketServer:
    """
    Run a server to handle messages.

    Attributes:
        logger (logging.Logger): Logger to log records.
        context (DaemonContext): Context for daemon process.
        listen (bool): Dose the server need keep listening
        actions (dict): Decide when receiving request with string, which method to respond it.

        CHECK_SOCKET_SERVER (str): request for check status of socket server.
        STOP_SOCKET_SERVER (str): request for stop socket server.

        SERVER_IS_RUNNING (str): status which means server is running.
        STOPPING_SERVER (str): status which means server is stopping.

    """

    def __init__(self, sock_host, sock_port):
        """
        Init class with parameters.
        Args:
            sock_host (str): IP Address to bind the server. "0.0.0.0" is supported.
            sock_port (int): The Port number for server listening on.
        """
        self.sock_host = sock_host
        self.sock_port = sock_port

        self.logger = logging.getLogger()
        self.context = DaemonContext()

        self.listen = True
        self.request_time_out = 60

        self.CHECK_SOCKET_SERVER, self.STOP_SOCKET_SERVER = 'CHECK_SOCKET_SERVER', 'STOP_SOCKET_SERVER'
        self.SERVER_IS_RUNNING, self.STOPPING_SERVER = 'SERVER_IS_RUNNING', 'STOPPING_SERVER'

        self.actions = {
            self.CHECK_SOCKET_SERVER: self.__check,
            self.STOP_SOCKET_SERVER: self.__shutdown
        }

    # functions in shell for call

    def startup(self):
        """
        Start socket server.And optional turn this process in to background daemon.
        Notes:
            This method will check if server is running first.
        """

        if self.ping():
            print 'Startup server [failed], Server already started.'
            return

        with self.context:
            print "starting server at %s:%d" % (self.sock_host, self.sock_port)
            self.logger.info("~~~~~~ starting server at %s:%d. ~~~~~~" % (self.sock_host, self.sock_port))
            self.__startup()

    def shutdown(self):
        """Send stop request to server."""
        if not self.ping():
            print 'server is not running, please start it first.'
            return

        self.logger.info("stopping server")
        print self.request(self.STOP_SOCKET_SERVER)

    def check(self):
        """Send check request to server."""
        self.logger.info("checking server")
        return self.request(self.CHECK_SOCKET_SERVER)

    def ping(self):
        """
        Test if socket server is running.
        Returns:
            bool: if socket is running.
        """
        self.logger.debug("testing if server is running")
        response = self.request(self.CHECK_SOCKET_SERVER)
        return response == self.SERVER_IS_RUNNING

    def request(self, request):
        """
        Open a client, connect to server and send request.
        Args:
            request (str): request string you want to send to server.
        Returns:
            str: response string from server. or error message generated by it self.
        """
        self.logger.debug("sending request to server with %s" % request)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((self.sock_host, self.sock_port))
            client_socket.settimeout(60)
            client_socket.send(request)
            response = client_socket.recv(1024)
        except socket.error as e:
            if e.errno == 111:
                response = "Can't connect to server."
            else:
                response = "Unknown Error [%s]: %s" % (type(e), e)
        finally:
            client_socket.close()

        self.logger.debug("get response from server with %s" % response)
        return response

    # functions in background daemon to response

    def __listen(self):
        """Start socket server and listening request!"""

        # get socket server
        self.logger.debug("init socket server")
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # how long to wait when restart.
        self.server_socket.bind((self.sock_host, self.sock_port))
        self.server_socket.listen(1)

        # keep socket server listening
        self.logger.debug("socket server start listening")
        while self.listen:
            connection, address = self.server_socket.accept()
            request = connection.recv(1024)

            self.logger.debug("send request %s to handler" % request)
            response = self.__handle(request)
            self.logger.debug("get response %s from handler" % response)
            connection.send(response)
            self.logger.debug("send response back to request.")

            if not self.listen:  # when stop keep listening.
                connection.close()
                self.logger.debug("socket server stopped")

    def __startup(self):
        """call child's _startup() and make server listening"""
        self.logger.debug("server starting in background.")

        # try to call child's _startup()
        try:
            self.logger.debug("calling child's _startup()")
            self._startup()
        except Exception as e:
            error_info = traceback.format_exc()
            self.logger.error("call child's _startup() failed: %s. Type is: %s" % (e, type(e)))
            self.logger.error("Traceback is %s" % error_info)
            raise
        else:
            self.logger.debug("child's _startup() done")

        self.__listen()

    def _startup(self):
        self.logger.debug("child class didn't overwrite this method.")

    def __handle(self, request):
        """
        Choice a right way to handle the request.
        Args:
            request (str): requested received from client.
        Returns:
            str: response string.
        """
        self.logger.debug("server handling request: %s." % request)

        if request in self.actions.keys():
            response = self.actions.get(request)()
        else:
            response = self._handle(request)

        self.logger.debug("child sending response: %s." % response)
        return response

    def _handle(self, request):
        """
        Need be overwrite by child class.
        Notes:
            Must return a str response.
        Args:
            request (str): requested received from client.
        Returns:
            str: response string.
        """
        return 'Parent Class is handling message.'

    def __check(self):
        """return server's status"""
        self.logger.debug("server checking.")
        return self.SERVER_IS_RUNNING

    def _check(self):
        self.logger.debug("child class didn't overwrite this method.")

    def __shutdown(self):
        """
        Call child's _shutdown(), turn off server's listen condition to close server
        Returns
            str: response to user.
        """
        self.logger.debug("server stopping.")

        # try to call child's _shutdown()
        try:
            self.logger.debug("calling child's _shutdown()")
            self._shutdown()
        except Exception as e:
            error_info = traceback.format_exc()
            self.logger.error("call child's _shutdown() failed: %s. Type is: %s" % (e, type(e)))
            self.logger.error("Traceback is %s" % error_info)
            return "Error when shutdown server."
        else:
            self.logger.debug("child's _shutdown() done")

        self.listen = False
        return self.STOPPING_SERVER

    def _shutdown(self):
        self.logger.debug("child class didn't overwrite this method.")
