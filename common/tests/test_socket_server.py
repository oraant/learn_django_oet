from django.test import TestCase
from common.libs.socket_server import SocketServer
from time import sleep


class MySocketServer(SocketServer):

    hello_request = "hello"
    joe_request = "joe"
    test_request = "test"

    hello_response = "Hello World~"
    joe_response = "Joe is handsome~"
    test_response = "Test successful~"

    def _handle(self, request):

        responses = {
            self.hello_request: self.hello_response,
            self.joe_request: self.joe_response,
            self.test_request: self.test_response
        }

        if request in responses.keys():
            return responses.get(request)
        else:
            return 'Sorry, I don\'t know what you are talking about.'


# todo : some open should be closed after raise exceptions like asserts
# todo : abnormal cases


class SocketServerTest(TestCase):

    def setUp(self):
        self.myss = MySocketServer('localhost', 15520)
        print '---------- 1'
        self.myss.start()
        print '---------- 2'

    def my_assert_equal(self, name, result, expect):
        print '------------', name
        print result
        self.assertEqual(result, expect)

    def my_assert_tf(self, name, result, expect):
        print '------------', name
        if expect:
            self.assertTrue(result)
        else:
            self.assertFalse(result)

    def test_function(self):

        print '------ start'
        self.myss.start()

        self.my_assert_tf(
            'test',
            self.myss.test(),
            True
        )

        sleep(1)

        self.my_assert_equal(
            'check',
            self.myss.check(),
            self.myss.SERVER_IS_RUNNING
        )

        self.my_assert_equal(
            'request hello',
            self.myss.request(self.myss.hello_request),
            self.myss.hello_response
        )

        self.my_assert_equal(
            'request joe',
            self.myss.request(self.myss.joe_request),
            self.myss.joe_response
        )

        self.my_assert_equal(
            'request test',
            self.myss.request(self.myss.test_request),
            self.myss.test_response
        )

        self.my_assert_equal(
            'stop',
            self.myss.stop(),
            self.myss.STOPPING_SERVER
        )

        self.my_assert_tf(
            'test',
            self.myss.test(),
            False
        )

        sleep(1)

        print '------ start'
        self.myss.start()

        self.my_assert_tf(
            'test',
            self.myss.test(),
            True
        )

        sleep(1)

        self.my_assert_equal(
            'stop',
            self.myss.stop(),
            self.myss.STOPPING_SERVER
        )

        self.my_assert_tf(
            'test',
            self.myss.test(),
            False
        )

        self.my_assert_equal(
            'check',
            self.myss.check(),
            self.myss.SERVER_IS_RUNNING
        )
