from data_handler import BaseHandler

class Handler(BaseHandler):

    def __init__(self):

        from puller.models import GlobalConfigs
        self.orm = GlobalConfigs

        self.fields = ['name','value','desc']

        self.datas = [
            ('mysql_host','127.0.0.1','Use 127.0.0.1 instead of localhost to enforce port'),
            ('mysql_port','3306','Will not work is host is localhost'),
            ('mysql_db','dbcache','-'),
            ('mysql_user','root','-'),
            ('mysql_password','123456','-'),

            ('redis_host','127.0.0.1','-'),
            ('redis_port','6379','-'),
            ('redis_db','0','-'),
            ('redis_password','','-'),
        ]
