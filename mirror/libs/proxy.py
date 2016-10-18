from common.libs.process_manager import MainJob
from mirror.libs.puller import Puller
from mirror.libs.cacher import Cacher
from mirror.libs.recorder import Recorder
from mirror.libs import exceptions as exc
from apscheduler.schedulers.background import BackgroundScheduler as Scheduler
from apscheduler.events import EVENT_JOB_ERROR


# todo : concurrent process config
# todo : sock file path
# todo : how long to wait if there are some error.


class Proxy(MainJob):
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

    def __init__(self, target_name, logger):
        """
        Init instance with parameters.

        Args:
            target_name (str): target oracle's name you want to mirror
            logger (logging.Logger): handle output logs
        """

        # init parent things.
        MainJob.__init__(self, logger)

        # init instance parameters
        self.target_name = target_name
        self.logger.debug('proxy init done.')


    def __prepare(self):
        """
        Prepare table_collection, scheduler.
        Get workers if they are all enabled and can be connect.
        """

        import mirror.models as models
        self.target = models.OracleTarget.objects.get(name=self.target_name)
        self.table_collection = getattr(models, self.target.table_collection).objects.all()
        self.logger.debug(
            "preparing oracle_target <%s> and table_collection <%s> done." % (
                self.target_name,
                self.target.table_collection
            )
        )

        self.scheduler = Scheduler()
        self.logger.debug("preparing scheduler done.")

        try:  # init cacher
            self.cacher = Cacher(self.target.mysql_server, self.target.mysql_db)
        except (exc.NotEnableError, exc.MySQLConnectError) as e:
            self.logger.error("Init %s's cacher failed: %s" % (self.target.name, e))
            raise
        else:
            self.logger.error("Init %s's cacher done." % self.target.name)

        try:  # init recorder
            self.recorder = Recorder(self.target.redis_server, self.target.redis_db)
        except (exc.NotEnableError, exc.ORACLEConnectError) as e:
            self.logger.error("Init %s's recorder failed: %s" % (self.target.name, e))
            self.__close_workers([self.cacher])
            raise
        else:
            self.logger.error("Init %s's recorder done." % self.target.name)

        try:  # init puller
            self.puller = Puller(self.target)  # if mysql and redis is ok, we connect to oracle.
        except (exc.NotEnableError, exc.ORACLEConnectError) as e:
            self.logger.error("Init %s's puller failed: %s" % (self.target.name, e))
            self.__close_workers([self.cacher, self.recorder])
            raise
        else:
            self.logger.error("Init %s's puller done." % self.target.name)

    def __close_workers(self, workers=None):
        """
        Close workers and record logs of the information.
        Args:
            workers (list): puller, cacher and recorder. If it none, then all there worker will be closed.
        """

        if not workers:
            workers = [self.cacher, self.recorder, self.puller]

        for worker in workers:
            msg = worker.close()
            self.logger.debug("closing %s: %s" % (str(worker), msg))

    def __schedule(self):
        """
        Generate jobs for every target table, and run it periodically under table.period
        """

        # add jobs
        self.logger.debug("adding jobs to scheduler.")
        for table in self.table_collection:
            name = "%s.%s" % (self.target.name, table.name)
            seconds = table.period.seconds

            # todo : next_run_time should be now for jobs.
            self.scheduler.add_job(self.__job, 'interval', args=(table,), name=name, seconds=seconds)
            self.logger.info("add job for %s, interval seconds is %s." % (name, seconds))
            self.scheduler.add_listener(self.__listener, EVENT_JOB_ERROR)  # todo : test for tmp

        self.logger.debug("jobs add done.")

        # run jobs
        try:
            self.logger.debug("starting scheduler.")
            self.scheduler.start()
            self.logger.debug("scheduler started successfully.")
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
        self.recorder.record(str(table.name), table.period.seconds)

    def __listener(self, event):  # todo : complete this.

        try:
            raise event.exception
        except Exception as e:
            self.logger.error(e)

    # overwrite father's method

    def run(self):
        """start scheduler in background thread."""
        self.__prepare()
        self.__schedule()

    def end(self):
        """stop scheduler, wait until all thread stopped."""
        self.scheduler.shutdown()
        self.__close_workers()

    def ping(self):
        """check job is running or not"""
        try:
            if self.scheduler.running:
                return True, 'job is running'
            else:
                return False, 'job is not running'
        except AttributeError:
            return False, 'job never run before'
