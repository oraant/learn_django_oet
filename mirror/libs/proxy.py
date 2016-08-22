from mirror.models import RedisServer, MySQLServer, OracleTarget
from mirror.libs import puller, cacher, recorder

class Proxy:

    def __init__(self, oracle_target):
        self.target = oracle_target

        exec "from mirror.models import " + self.target.tables
        self.tables = eval(self.target.tables).objects.all()
        map(self._format,self.tables)

        self.cacher = cacher.Cacher(mysql_dsn)
        self.puller = puller.Puller(oracle_dsn)
        self.verify = recorder.Verify(redis_dsn)

    def _get_configs(self):
        mysql_dsn = MySQLServer.objects.filter(enable=True)
        redis_dsn = RedisServer.objects.filter(enable=True)
        oracle_dsn = MySQLServer.objects.filter(enable=True)

    def run(self, table):
        '''pull and cache,record in redis,and write logs'''

        try:
            datas = self.puller.pull(table)
        except Exception as e:
            print e
            return

        try:
            self.cacher.cache(table,datas)
        except Exception as e:
            print e
            return

        try:
            self.verify.record(table.name)
        except Exception as e:
            print e
            return

    def schedule(self):
        '''schedule jobs for every table'''
        scheduler = Scheduler()
        for table in self.tables:
            print 'scheduler adding'
            scheduler.add_job(self._main, 'interval',args=(table,), seconds=table.period)
            print 'scheduler added'

        try:
            scheduler.start()
        except Exception,e:
            print '===',Exception,e
            print '=== an error occured,outing'
        except KeyboardInterrupt,e:
            print '===',KeyboardInterrupt,e
            print '=== you want to stop,outing'
        finally:
            self.cacher.close()
            self.puller.close()
