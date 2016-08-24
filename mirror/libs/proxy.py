from sys import exit
from importlib import import_module
from mirror.libs import puller, cacher, recorder
from mirror.libs import exceptions as exc
from apscheduler.schedulers.blocking import BlockingScheduler as Scheduler


class Proxy(object):
    """
    Proxy to handle

    Args:
        target (mirror.models.OracleTarget): target oracle want to mirror
        logger (logging.Logger): handle output logs

    Attributes:
        puller (puller.Puller): pull data from target database's tables.
        cacher (cacher.Cacher): cache data into mysql server.
        recorder (recorder.Recorder): record cache status into redis server.
        scheduler (Scheduler): Scheduler to run jobs periodically.

    Raises:
        exc.NotEnableError: If one of the three workers (cacher, recorder, puller) is not enable.
            Proxy will log it and end itself's job.
    """

    def __init__(self, target, logger):

        # init instance parameters
        self.target = target
        self.logger = logger
        self.tables = import_module("mirror.models.%s" % target.tables)  # todo: models * should change to getattr
        self.scheduler = Scheduler()

        # get workers if they are all enabled and connectable
        try:
            self.puller = puller.Puller(self.target)
            self.cacher = cacher.Cacher(self.target.mysql)
            self.recorder = recorder.Verify(self.target.redis)

        except exc.NotEnableError as e:

            msg = "Worker of Oracle Target <%s> is not Enabled,Error msg is: <%s>" % (target.name, e)
            self.logger.error(msg)

            exit(1)  # todo: does exit can break the scheduler?

        except (exc.ORACLEConnectError, exc.MySQLConnectError, exc.RedisConnectError) as e:

            self.puller.close()
            self.cacher.close()
            self.recorder.close()

            msg = "Worker of Oracle Target <%s> can't connect,Error msg is: <%s>" % (target.name, e)
            self.logger.error(msg)

            exit(1)

        # run the scheduler.
        self._schedule()

    def _schedule(self):
        """
        Generate jobs for every target table, and run it periodically under table.period
        """

        # add jobs
        for table in self.tables:
            name = "%s.%s" % (self.target.name, table.name)
            seconds = table.period.seconds

            self.scheduler.add_job(self._job, 'interval', args=(table,), name=name, seconds=seconds)
            self.logger.info("add job for %s, interval seconds is %s." % (name, seconds))

        # run jobs
        try:
            self.scheduler.start()
        except Exception as e:
            self.logger.error(e)
        finally:
            self.cacher.close()
            self.puller.close()
            self.recorder.close()

    def _job(self, table):
        """
        A job running under a cron scheduler.
        Pull and cache data from target table into mysql server,and record status into redis server.

        Args:
            table (mirror.models.TableSQL): target table want to pull from target oracle.
        """

        data = self.puller.pull(table)
        self.cacher.cache(table, data)
        self.recorder.record(table.name, table.period)