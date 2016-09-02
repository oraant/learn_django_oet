
from multiprocessing import Process, Pipe
from time import sleep


class ProcessManager:
    """
    This class will create a child process and do the main jobs, and manage children with father's method.

    Attributes:
        listen (bool):
        running (bool):
        gap_time (int): when restart main job, the gap time you want to wait between stop and start.Unit is seconds.

        parent (_multiprocessing.Connection):
        child (_multiprocessing.Connection):

        process (multiprocessing.process.Process):

        cls.START (str):
        cls.STOP (str):
        cls.RESTART (str):
        cls.STATUS (str):

    Examples:
        from apscheduler.schedulers.background import BackgroundScheduler as Scheduler
        from time import sleep

        class ScheduleJobs(ProcessManager):
            def __init__(self, name):
                self.name = name
                ProcessManager.__init__(self)

            def _set_logger(self):
                import logging
                logging.basicConfig()

            def _output(self, msg="hello"):
                print msg, self.name
                sleep(3)
                raise KeyError('haha')

            def _run(self):
                self._set_logger()
                self.scheduler = Scheduler()
                self.scheduler.add_job(self._output, 'interval', seconds=10)
                self.scheduler.start()

            def _terminate(self):
                self.scheduler.shutdown()

        sj = ScheduleJobs('sj1')
        sj.start()

    """

    START, STOP, STATUS, RESTART = 'START', 'STOP', 'STATUS', 'RESTART'

    # method for subclass

    def __init__(self):  #
        """
        Must at end, because it will block child's code, and wait for pipe msg.
        Attributes

        """
        self.parent, self.child = Pipe()

        self.listen = True
        self.running = False
        self.gap_time = 0

        self.process = Process(target=self._listen)
        self.process.start()

    def _run(self):
        """Your code here. Make sure the code run in daemon."""
        pass

    def _terminate(self):
        """Your code here. End the code running in daemon."""
        pass

    # method for child process.

    def _listen(self):
        operations = {
            self.START: self._start,
            self.STOP: self._stop,
            self.RESTART: self._restart,
            self.STATUS: self._status
        }

        while self.listen:
            msg = self.child.recv()
            if msg in operations.keys():
                operations.get(msg)()
            else:
                self.child.send("Invalid Command.")

    def _start(self):
        if self.running:
            self.child.send("child process already running")
            return

        self._run()
        self.listen = True
        self.running = True
        print '---> ', self.running

    def _stop(self):
        """
        Stop child process's main job by call it's _terminate().
        Stop child process's listener by change the self.listen variable after child's main job terminated.
        """
        self._terminate()
        self.listen = False
        self.running = False
        print '---< ', self.running

    def _restart(self):
        """
        Restart the child process.
        Note that self.listen and self.running changed to False first, then changed to True before listener stop.
        """
        self._stop()
        sleep(self.gap_time)
        self._start()

    def _status(self):
        print '---? ', self.running
        if self.running:
            self.child.send("child process is running")
        else:
            self.child.send("child process is not running")

    # method for father process.

    def start(self):
        self.parent.send(self.START)

    def stop(self):
        self.parent.send(self.STOP)

    def restart(self):
        self.parent.send(self.RESTART)

    def status(self):
        self.parent.send(self.STATUS)
        if self.parent.poll(0.1):
            return self.parent.recv()
        else:
            return 'child is not running -'


from apscheduler.schedulers.background import BackgroundScheduler as Scheduler
from apscheduler.events import EVENT_JOB_ERROR
from datetime import datetime
from time import sleep
from apscheduler.executors.pool import ThreadPoolExecutor
import threading

class ScheduleJobs(ProcessManager):

    def __init__(self, name):
        self.name = name
        ProcessManager.__init__(self)

    def _set_logger(self):
        #import logging
        #logging.basicConfig()
        pass

    def _output(self, msg="hello"):
        print msg, self.name
        raise KeyError('haha')

    def _exc_handler(self, event):
        if not event.exception:
            return

        try:
            raise event.exception
        except Exception as e:
            threading.current_thread().name = 'listener'
            print "I got Error! It's ", type(e), e
            print "restarting it self for 5s"
            self.gap_time = 5
            self.restart()
            print "restart done"
            sleep(3)
            print self.status()

    def _run(self):
        self._set_logger()
        executors = {'default': ThreadPoolExecutor(3)}
        self.scheduler = Scheduler(executors=executors)
        self.scheduler.add_job(self._output, 'interval', seconds=2, next_run_time=datetime.now())
        self.scheduler.add_listener(self._exc_handler, EVENT_JOB_ERROR)
        self.scheduler.start()

    def _terminate(self):
        self.scheduler.shutdown(wait=False)


sj = ScheduleJobs('sj1')
sj.start()

while True:
    #print 'this is father'
    sleep(1)