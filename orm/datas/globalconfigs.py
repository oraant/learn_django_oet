from handler import BasicHandler


class Handler(BasicHandler):

    """Handle data with GlobalConfigs."""

    def __init__(self):

        from mirror.models import GlobalConfigs
        self.orm = GlobalConfigs

        self.fields = ['name', 'value', 'desc']

        self.data = [
            ('mysql_host', '127.0.0.1', 'Use 127.0.0.1 instead of localhost to enforce port'),
            ('mysql_port', '3306', 'Will not work if host is localhost'),
            ('mysql_db', 'oet', '-'),
            ('mysql_user', 'django', '-'),
            ('mysql_password', 'django', '-'),

            ('redis_host', '127.0.0.1', '-'),
            ('redis_port', '6379', '-'),
            ('redis_db', '0', '-'),
            ('redis_password', '', '-'),
        ]
