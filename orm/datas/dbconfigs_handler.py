from data_handler import BaseHandler

class Handler(BaseHandler):

    def __init__(self):

        from puller.models import DBConfigs
        self.orm = DBConfigs

        self.fields = [ 'name','enable','desc',
                        'version','rac','dbid','instance',' ip','port',
                        'user','password','service',
                        'tables','points']

        self.datas= [(
                        'db11g',True,'-',
                        '11.2.0.1',False,'363264677',1,
                        '192.168.18.129','1521',
                        'system','oracle','db11g',
                        'PTOra11gR2','-'
                    ),(
                        'fakedb',False,'-',
                        '11.2.0.1',False,'363264677',1,
                        '192.168.18.139','1521',
                        'system','oracle','db11g',
                        'PTOra11gR2','-'
                    ),(
                        'fakedb2',False,'-',
                        '11.2.0.1',False,'363264677',1,
                        '192.168.18.149','1521',
                        'system','oracle','db11g',
                        'PTOra11gR2','-'
                    ),]
