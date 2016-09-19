from argparse import ArgumentParser
from mirror.libs.proxy import Proxy
from mirror.models import OracleTarget


class Handler:

    def __init__(self):

        self.proxies = dict()

        for target in OracleTarget.objects.all():
            name = target.name
            proxy = Proxy(target)
            self.proxies.update(name=proxy)

    def handle(self, request):
        """
        Args:
            request (str):

        Returns:
            response (str): response for request.
        """

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
            "status": proxy.status,
        }

        return operations.get(function)()