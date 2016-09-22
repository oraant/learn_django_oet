from daemon import DaemonContext
import socket


class SocketServer:
    """
    Run a server to handle messages.

    Attributes:
        listen (bool): Dose the server need keep listening
        actions (dict): Decide when receiving request with string, which method to respond it.
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

        self.listen = True

        self.CHECK_SOCKET_SERVER, self.STOP_SOCKET_SERVER = 'CHECK_SOCKET_SERVER', 'STOP_SOCKET_SERVER'
        self.SERVER_IS_RUNNING, self.STOPPING_SERVER = 'SERVER_IS_RUNNING', 'STOPPING_SERVER'

        self.actions = {
            self.CHECK_SOCKET_SERVER: self.__check,
            self.STOP_SOCKET_SERVER: self.__stop
        }

    # functions in shell for call

    def start(self, daemon=True):
        """
        Start socket server.
        Args:
            daemon (bool): Running the server in background daemon of not.
        """
        if daemon:
            with DaemonContext():
                self.__start()
        else:
            self.__start()

    def request(self, request):
        """
        Try to send request to socket server.

        Args:
            request (str): request string you want to send to server.

        Returns:
            str: response string from server. or error message generated by it self.

        Raises:
            socket.error: Unknown socket error occurred.
        """
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((self.sock_host, self.sock_port))
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

    def stop(self):
        """Send stop request to server."""
        return self.request(self.STOP_SOCKET_SERVER)

    def check(self):
        """Send check request to server."""
        return self.request(self.CHECK_SOCKET_SERVER)

    def test(self):
        """
        Test if socket server is running.
        Returns:
            bool: if socket is running.
        """
        response = self.request(self.CHECK_SOCKET_SERVER)
        if response == self.SERVER_IS_RUNNING:
            return True
        else:
            return False

    # functions in background daemon to response

    def __start(self):
        """Start socket server and listening request!"""

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # make server can be restart immediately.
        server_socket.bind((self.sock_host, self.sock_port))
        server_socket.listen(1)

        while self.listen:
            connection, address = server_socket.accept()
            request = connection.recv(1024)

            response = self.__handle(request)
            connection.send(response)

            if not self.listen:
                connection.close()

    def __handle(self, request):
        """
        Choice a right way to handle the request.

        Args:
            request (str): requested received from client.

        Returns:
            str: response string.
        """

        if request in self.actions.keys():
            return self.actions.get(request)()
        else:
            return self._handle(request)

    def __check(self):
        return self.SERVER_IS_RUNNING

    def __stop(self):
        """Close server and respond request."""
        self.listen = False
        return self.STOPPING_SERVER

    # functions for child classes to overwrite.

    def _handle(self, request):
        return 'this is handle~'
