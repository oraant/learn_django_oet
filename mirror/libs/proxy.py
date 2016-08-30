from sys import exit
from importlib import import_module
from mirror.libs import puller, cacher, recorder
from mirror.libs import exceptions as exc
import mirror.models as models
from apscheduler.schedulers.blocking import BlockingScheduler as Scheduler


class Proxy(object):
    """
    Proxy to handle the main mirror job for a oracle database.

    Attributes:
        target (mirror.models.OracleTarget): target oracle want to mirror.
        table_collection (mirror.models.TableCollections): tables want to mirror.

        logger (logging.Logger): handle output logs.
        scheduler (Scheduler): Scheduler to run jobs periodically.

        puller (puller.Puller): pull data from target database's tables.
        cacher (cacher.Cacher): cache data into mysql server.
        recorder (recorder.Recorder): record cache status into redis server.

    Raises:
        exc.NotEnableError: If one of the three workers (cacher, recorder, puller) is not enable.
            Proxy will log it and end itself's job.
    """

    def __init__(self, target, logger):
        """
        Init instance with parameters.

        Args:
            target (mirror.models.OracleTarget): target oracle want to mirror
            logger (logging.Logger): handle output logs
        """

        # init instance parameters
        self.target = target
        self.logger = logger
        self.table_collection = getattr(models, self.target.table_collection)
        self.scheduler = Scheduler()

    def _get_workers(self):
        """Get workers if they are all enabled and connectable"""

        try:
            self.cacher = cacher.Cacher(self.target.mysql, self.target.mysql_db)
            self.recorder = recorder.Recorder(self.target.redis, self.target.redis_db)
            self.puller = puller.Puller(self.target)  # if mysql and redis is ok, we connect to them.
        except exc.NotEnableError as e:
            self.logger.error("[%s] Worker Not Enabled. Error: %s" % (self.target.name, e))
            self._close_workers()
        except (exc.ORACLEConnectError, exc.MySQLConnectError, exc.RedisConnectError) as e:
            self.logger.error("[%s] Worker Can't connect. Error: %s" % (self.target.name, e))
            self._close_workers()

    def _close_workers(self):
        """Close workers and record logs of the information."""

        msg = self.puller.close()
        self.logger.info(msg)

        msg = self.cacher.close()
        self.logger.info(msg)

        msg = self.recorder.close()
        self.logger.info(msg)

    def _run_schedule(self):
        """
        Generate jobs for every target table, and run it periodically under table.period
        """

        # add jobs
        for table in self.table_collection:
            name = "%s.%s" % (self.target.name, table.name)
            seconds = table.period.seconds

            self.scheduler.add_job(self._job_for_table, 'interval', args=(table,), name=name, seconds=seconds)
            self.logger.info("add job for %s, interval seconds is %s." % (name, seconds))

        # run jobs
        try:
            self.scheduler.start()
        except Exception as e:
            self.logger.error(e)
        finally:

    def _job_for_table(self, table):
        """
        A job running under a cron scheduler.
        Pull and cache data from target table into mysql server,and record status into redis server.

        Args:
            table (mirror.models.TableCollections): target table want to pull from target oracle.
        """

        data = self.puller.pull(table)
        self.cacher.cache(table, data)
        self.recorder.record(table.name, table.period.seconds)


    def start(self):
        self._get_workers()
        self._schedule()

    def stop(self):
        self._close_workers()

    def restart(self):
