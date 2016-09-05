
from multiprocessing import Process, Pipe
from time import sleep
from threading import Thread, Timer, Event


class ProcessManager:
    """
    This class will create a child process and do the main jobs, and manage children with father's method.
    This class fit with the situation when a man manager processes with command line.
    Doesn't support multi-concurrence manager operations.

    Attributes:
        listen (bool):
        status (str):
        event_suspend_down (threading.Event):

        parent (_multiprocessing.Connection):
        child (_multiprocessing.Connection):

        process (multiprocessing.process.Process):

        cls.START (str):
        cls.STOP (str):
        cls.RESTART (str):
        cls.STATUS (str):
        cls.SUSPEND (str):

        cls.STARTING (str):
        ...

    """

    START, STOP, STATUS, RESTART, REBORN = 'START', 'STOP', 'STATUS', 'RESTART', 'REBORN'
    STARTING, RUNNING, STOPPING, STOPPED, SUSPENDED = 'STARTING', 'RUNNING', 'STOPPING', 'STOPPED', 'SUSPENDED'

    # method for subclass

    def __init__(self):  #
        """
        Must at end, because it will block child's code, and wait for pipe msg.
        Attributes

        """
        self.parent, self.child = Pipe()

        self.listen = True
        self.status = self.STOPPED
        self.event_suspend_down = Event()

        self.process = Process(target=self._listen)
        self.process.start()

    def _run(self):
        """Your code here"""
        pass

    def _terminate(self):
        """Your code here"""
        pass

    # method for child process.

    def _listen(self):  # the main thread running in child process.
        operations = {
            self.START: self._start,
            self.STOP: self._stop,
            self.RESTART: self._restart,
            self.STATUS: self._status,
            self.REBORN: self._reborn
        }

        while self.listen:
            msg = self.child.recv()  # blocking and wait.
            if msg['method'] in operations.keys():
                if 'arg' in msg.keys():
                    result = operations.get(msg['method'])(*msg['arg'])
                else:
                    result = operations.get(msg['method'])()
            else:
                result = "Invalid Command."
            self.child.send(result)

    def _start(self, *args):  # todo : optimize with map method, maybe.
        """
        Starting child process's main job by call it's _run() in a new thread.
        Args:
            *args: useless, just be compatible with self._listen()

        Returns:
            str: explain how's it going.
        """
        def _start_handler():
            self._run()
            self.status = self.RUNNING

        if self.status == self.STOPPED:  # start job
            self.status = self.STARTING
            self.listen = True  # listen maybe closed by _stop(), so open it every time _start()
            Thread(target=_start_handler, name="calling start").start()
            msg = "Trying to start child process's job"
        elif self.status in [self.RUNNING, self.STARTING]:
            msg = "child process already running"
        elif self.status == self.STOPPING:
            msg = "child process is busying to stop, please try again later"
        elif self.status == self.REBORN:
            msg = "child process is wait for reborn.Recall reborn to cancel it."
        else:
            msg = "Some error occurred. Job status is unknown as %s" % self.status

        return msg

    def _stop(self, *args, **kwargs):
        """
        Stop child process's main job by call it's _terminate() in a new non-daemon thread.
        Stop child process's listener by change the self.listen variable after child's main job terminated.
        """

        def _stop_handler():
            self._terminate()
            self.status = self.STOPPED
            if "event" in kwargs:  # if calling by restart or reborn, notice them this is done.
                kwargs['event'].set()

        if self.status == self.RUNNING:  # stop job
            self.listen = False
            self.status = self.STOPPING
            Thread(target=_stop_handler, name="calling stop").start()
            msg = "Trying to stop Child process's job."
        elif self.status in [self.STOPPING, self.STOPPED]:
            msg = "child process already stopped"
        elif self.status == self.STARTING:
            msg = "child process is busying to start, please try again later."
        elif self.status == self.SUSPENDED:
            msg = "child process is wait for reborn.Recall reborn to cancel it."
        else:
            msg = "Some error occurred. Job status is unknown as %s" % self.status

        return msg

    def _restart(self, *args):
        """
        Restart the child process.
        Note that self.listen and self.running changed to False first, then changed to True before listener stop.
        """

        def _restart_handler():
            stop_event = Event()
            self._stop(event=stop_event)

            stop_event.wait()
            self._start()

        if self.status == self.RUNNING:  # restart job
            Thread(target=_restart_handler, name="calling restart").start()
            msg = "Trying to restart Child process's job."
        elif self.status == self.STOPPED:  # start job
            self._start()
            msg = "Child process's job is not running.Trying to start it."
        elif self.status == self.STARTING:
            msg = "child process is busying to start, please try again later."
        elif self.status == self.STOPPING:
            msg = "child process is busying to stop, please try again later"
        elif self.status == self.SUSPENDED:
            msg = "child process is wait for reborn.Recall reborn to cancel it."
        else:
            msg = "Some error occurred. Job status is unknown as %s" % self.status

        return msg

    def _reborn(self, time):

        # todo : create a timer(or wait event thread) at first time, close it at next time.

        def _suspend_start():
            Timer(self.time, self._start, name="suspend_start")

        if self.status == self.RUNNING:  # restart job
            msg = "Trying to reborn Child process's job."
        elif self.status == self.STOPPED:  # start job
            self._start()
            msg = "Child process's job is not running.Trying to reborn it."
        elif self.status == self.SUSPENDED:
            msg = "Canceled suspend start for child process's job."
        elif self.status == self.STARTING:
            msg = "child process is busying to start, please try again later."
        elif self.status == self.STOPPING:
            msg = "child process is busying to stop, please try again later"
        else:
            msg = "Some error occurred. Job status is unknown as %s" % self.status


        return msg

    def _status(self, *args):
        msg = "child process's job status is %s" % self.status
        return msg

    # method for father process.

    def start(self):
        msg = {'method': self.START}
        self.parent.send(msg)

    def stop(self):
        msg = {'method': self.STOP}
        self.parent.send(msg)

    def restart(self):
        msg = {'method': self.RESTART}
        self.parent.send(msg)

    def status(self):
        msg = {'method': self.STATUS}
        self.parent.send(msg)
        if self.parent.poll(0.1):
            return self.parent.recv()
        else:
            return 'can not find child.'

    def reborn(self, time=10):
        msg = {'method': self.REBORN, 'arg': time}
        self.parent.send(msg)

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
        import logging
        logging.basicConfig()
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