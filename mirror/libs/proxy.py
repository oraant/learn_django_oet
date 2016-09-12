from common.libs.process_manager import ProcessManager
from mirror.libs.puller import Puller
from mirror.libs.cacher import Cacher
from mirror.libs.recorder import Recorder
from mirror.libs import exceptions as exc
import mirror.models as models
from apscheduler.schedulers.blocking import BlockingScheduler as Scheduler


# todo : concurrent process config
# todo : sock file path
# todo : how long to wait if there are some error.


class Proxy(ProcessManager):
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

        # init parent things.
        ProcessManager.__init__(self)

    def __prepare(self):
        """Prepare workers, table_collection, and scheduler."""

        self.table_collection = getattr(models, self.target.table_collection)
        self.scheduler = Scheduler()

        # Get workers if they are all enabled and connectable
        try:
            self.cacher = Cacher(self.target.mysql_server, self.target.mysql_db)
            self.recorder = Recorder(self.target.redis_server, self.target.redis_db)
            self.puller = Puller(self.target)  # if mysql and redis is ok, we connect to them.
        except exc.NotEnableError as e:
            self.logger.error("[%s] Worker Not Enabled. Error: %s" % (self.target.name, e))
            self.__close_workers()
        except (exc.ORACLEConnectError, exc.MySQLConnectError, exc.RedisConnectError) as e:
            self.logger.error("[%s] Worker Can't connect. Error: %s" % (self.target.name, e))
            self.__close_workers()

    def __close_workers(self):
        """Close workers and record logs of the information."""

        msg = self.puller.close()
        self.logger.info(msg)

        msg = self.cacher.close()
        self.logger.info(msg)

        msg = self.recorder.close()
        self.logger.info(msg)

    def __schedule(self):
        """
        Generate jobs for every target table, and run it periodically under table.period
        """

        # add jobs
        for table in self.table_collection:
            name = "%s.%s" % (self.target.name, table.name)
            seconds = table.period.seconds

            # todo : next_run_time should be now for jobs.
            self.scheduler.add_job(self.__job, 'interval', args=(table,), name=name, seconds=seconds)
            self.logger.info("add job for %s, interval seconds is %s." % (name, seconds))

        # run jobs
        try:
            self.scheduler.start()
        except Exception as e:
            self.logger.error(e)
            self.scheduler.shutdown()

    def __job(self, table):
        """
        A job running under a cron scheduler.
        Pull and cache data from target table into mysql server,and record status into redis server.

        Args:
            table (mirror.models.TableCollections): target table want to pull from target oracle.
        """

        data = self.puller.pull(table)
        self.cacher.cache(table, data)
        self.recorder.record(table.name, table.period.seconds)

    def __listener(self, event):

        if not event.exception:
            return

        try:
            raise event.exception
        except Exception as e:
            pass

    # overwrite father's method

    def _start(self):
        self.__prepare()
        self.__schedule()

    def _stop(self):
        self.scheduler.shutdown()
        self.__close_workers()
