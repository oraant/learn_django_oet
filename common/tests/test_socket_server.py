from django.test import TestCase
from time import sleep
from django.core.management import call_command
from django.utils.six import StringIO
from common.management.commands.test_socket_server import MySocketServer
from os import popen


# todo : some open should be closed after raise exceptions like asserts
# todo : abnormal cases


class SocketServerTest(TestCase):
    def setUp(self):
        self.manager = '/product/oet/manage.py'
        self.myss = MySocketServer('', 123)

    def my_assert_equal(self, args, expect):

        command = 'python %s test_socket_server %s' % (self.manager,  args)
        print '------------', command

        result = popen(command)
        output = result.readlines()

        if not output and not expect:
            self.assertEqual(0, 0)
            return

        result = output[0].strip()
        self.assertEqual(result, expect)

    def test_function(self):

        self.my_assert_equal('start', '')

        self.my_assert_equal('test', 'True')

        sleep(1)

        self.my_assert_equal('check', self.myss.SERVER_IS_RUNNING)

        self.my_assert_equal('request %s' % self.myss.hello_request, self.myss.hello_response)

        self.my_assert_equal('request %s' % self.myss.joe_request, self.myss.joe_response)

        self.my_assert_equal('request %s' % self.myss.test_request, self.myss.test_response)

        self.my_assert_equal('stop', self.myss.STOPPING_SERVER)

        self.my_assert_equal('test', 'False')

        sleep(1)

        self.my_assert_equal('start', '')

        self.my_assert_equal('test', 'True')

        sleep(1)

        self.my_assert_equal('stop', self.myss.STOPPING_SERVER)

        self.my_assert_equal('test', 'False')

        self.my_assert_equal('check', '[Errno 111] Connection refused')
