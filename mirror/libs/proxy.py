from mirror.libs import puller, cacher, recorder, exceptions
from sys import exit
from apscheduler.schedulers.blocking import BlockingScheduler as Scheduler


class Proxy:

    """
    
    """

    def __init__(self, oracle_target, logger):

        """
        Init things...

        :param oracle_target: instance of OracleTarget model
        :param logger: handle output logs
        """

        # get oracle target
        self.target = oracle_target
        self.logger = logger

        # get tables to pull
        exec "from mirror.models import " + self.target.tables
        self.tables = eval(self.target.tables).objects.all()

        # get workers if they are all enabled
        try:
            self.cacher = cacher.Cacher(self.target.mysql)
            self.recorder = recorder.Verify(self.target.redis)
            self.puller = puller.Puller(self.target)
        except exceptions.NotEnableError as e:
            self.logger.warning(e)
            exit(1)

    def run(self, table):
        """
        pull and cache,record in redis,and write logs

        :param table:
        :return:
        """

        datas = self.puller.pull(table)
        self.cacher.cache(table,datas)
        self.verify.record(table.name)

    def schedule(self):
        """schedule jobs for every table"""
        scheduler = Scheduler()
        for table in self.tables:
            print 'scheduler adding'
            scheduler.add_job(self._main, 'interval',args=(table,), seconds=table.period)
            print 'scheduler added'

        try:
            scheduler.start()
        except Exception as e:
            print '===', e
            print '=== an error occured,outing'
        except KeyboardInterrupt as e:
            print '===', e
            print '=== you want to stop,outing'
        finally:
            self.cacher.close()
            self.puller.close()
