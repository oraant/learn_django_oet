from django.test import TestCase
from common.libs import socket_server
import daemon

# todo : some open should be closed after raise exceptions like asserts
# todo : abnormal cases


class SocketServerTest(TestCase):

    def setUp(self):
        self.server = socket_server.SocketServer('localhost', 15521)

    def test_function(self):
        self.server.start_server()
        