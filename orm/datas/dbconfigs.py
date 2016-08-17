from handler import BasicHandler


class Handler(BasicHandler):

    """Handle data with DBConfigs."""

    def __init__(self):

        from orm.models import DBConfigs
        self.orm = DBConfigs

        self.fields = [
            'name', 'enable', 'desc',
            'version', 'rac', 'dbid', 'instance', ' ip', 'port',
            'user', 'password', 'service',
            'tables', 'points'
        ]

        self.data = [
            (
                'db11g', True, '-',
                '11.2.0.1', False, '363264677', 1,
                '192.168.18.129', '1521',
                'system', 'oracle', 'db11g',
                'PTOra11gR2', '-'
            ), (
                'fakedb', False, '-',
                '11.2.0.1', False, '363264677', 1,
                '192.168.18.139', '1521',
                'system', 'oracle', 'db11g',
                'PTOra11gR2', '-'
            ), (
                'fakedb2', False, '-',
                '11.2.0.1', False, '363264677', 1,
                '192.168.18.149', '1521',
                'system', 'oracle', 'db11g',
                'PTOra11gR2', '-'
            ),
        ]
