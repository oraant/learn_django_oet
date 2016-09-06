
from multiprocessing import Process, Pipe
from time import sleep
from threading import Thread, Timer, Event


class ProcessManager:  # change to protect function to avoid children class overwrite it attributes.
    """
    This class will create a child process and do the main jobs, and manage children with father's method.
    This class fit with the situation when a man manager processes with command line.
    Doesn't support multi-concurrence manager operations.

    Attributes:  # todo : commplete this.
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
        self.__parent, self.__child = Pipe()

        self.__need_listen = True
        self.__status = self.STOPPED
        self.__suspend_start_timer = None

        self.__process = Process(target=self._listen)
        self.__process.start()

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

        while self.__need_listen:
            msg = self.__child.recv()  # blocking and wait.
            if msg['method'] in operations.keys():
                if 'arg' in msg.keys():
                    result = operations.get(msg['method'])(*msg['arg'])
                else:
                    result = operations.get(msg['method'])()
            else:
                result = "Invalid Command."
            self.__child.send(result)

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
            self.__status = self.RUNNING

        if self.__status == self.STOPPED:  # start job
            self.__status = self.STARTING
            self.__need_listen = True  # listen maybe closed by _stop(), so open it every time _start()
            Thread(target=_start_handler, name="calling start").start()
            msg = "Trying to start child process's job"
        elif self.__status in [self.RUNNING, self.STARTING]:
            msg = "child process already running"
        elif self.__status == self.STOPPING:
            msg = "child process is busying to stop, please try again later"
        elif self.__status == self.REBORN:
            msg = "child process is wait for reborn.Recall reborn to cancel it."
        else:
            msg = "Some error occurred. Job status is unknown as %s" % self.__status

        return msg

    def _stop(self, *args, **kwargs):
        """
        Stop child process's main job by call it's _terminate() in a new non-daemon thread.
        Stop child process's listener by change the self.listen variable after child's main job terminated.
        """

        def _stop_handler():
            self._terminate()
            self.__status = self.STOPPED
            if "event" in kwargs:  # if calling by restart or reborn, notice them this is done.
                kwargs['event'].set()

        if self.__status == self.RUNNING:  # stop job
            self.__need_listen = False
            self.__status = self.STOPPING
            Thread(target=_stop_handler, name="calling stop").start()
            msg = "Trying to stop Child process's job."
        elif self.__status in [self.STOPPING, self.STOPPED]:
            msg = "child process already stopped"
        elif self.__status == self.STARTING:
            msg = "child process is busying to start, please try again later."
        elif self.__status == self.SUSPENDED:
            msg = "child process is wait for reborn.Recall reborn to cancel it."
        else:
            msg = "Some error occurred. Job status is unknown as %s" % self.__status

        return msg

    def _restart(self, *args):
        """
        Restart the child process.
        Note that self.listen and self.running changed to False first, then changed to True before listener stop.
        """

        def _restart_handler():  # will block for a will
            stop_event = Event()
            self._stop(event=stop_event)

            stop_event.wait()
            self._start()

        if self.__status == self.RUNNING:  # restart job
            Thread(target=_restart_handler, name="calling restart").start()
            msg = "Trying to restart Child process's job."
        elif self.__status == self.STOPPED:  # start job
            self._start()
            msg = "Child process's job is not running.Trying to start it."
        elif self.__status == self.STARTING:
            msg = "child process is busying to start, please try again later."
        elif self.__status == self.STOPPING:
            msg = "child process is busying to stop, please try again later"
        elif self.__status == self.SUSPENDED:
            msg = "child process is wait for reborn.Recall reborn to cancel it."
        else:
            msg = "Some error occurred. Job status is unknown as %s" % self.__status

        return msg

    def _reborn(self, time):

        # todo : create a timer(or wait event thread) at first time, close it at next time.

        def _suspend_handler():
            if self.__suspend_start_timer:  # todo : can be removed after test.
                print "internal error: suspending start, but instance variable is busy."  # todo : a log is better.
                return

            def _suspend():
                self._start()
                self.__suspend_start_timer = None

            t = Timer(self.time, _suspend, name="suspend_start")
            self.__suspend_start_timer = t
            t.start()

        def _reborn_handler():  # block for a while
            stop_event = Event()
            self._stop(event=stop_event)
            stop_event.wait()
            _suspend_handler()

        def _cancel_handler():
            if not self.__suspend_start_timer:
                print "internal error: suspending canceling, but instance variable is None."  # todo : a log is better.
                return

            self.__suspend_start_timer.cancel()
            self.__suspend_start_timer = None

        if self.__status == self.RUNNING:  # restart job
            _reborn_handler()
            msg = "Trying to reborn Child process's job."
        elif self.__status == self.STOPPED:  # start job
            _suspend_handler()
            msg = "Child process's job is not running.Trying to reborn it."
        elif self.__status == self.SUSPENDED:
            _cancel_handler()
            msg = "Canceled suspend start for child process's job."
        elif self.__status == self.STARTING:
            msg = "child process is busying to start, please try again later."
        elif self.__status == self.STOPPING:
            msg = "child process is busying to stop, please try again later"
        else:
            msg = "Some error occurred. Job status is unknown as %s" % self.__status

        return msg

    def _status(self, *args):
        msg = "child process's job status is %s" % self.__status
        return msg

    # method for father process.

    def start(self):
        msg = {'method': self.START}
        self.__parent.send(msg)

    def stop(self):
        msg = {'method': self.STOP}
        self.__parent.send(msg)

    def restart(self):
        msg = {'method': self.RESTART}
        self.__parent.send(msg)

    def status(self):
        msg = {'method': self.STATUS}
        self.__parent.send(msg)
        if self.__parent.poll(0.1):
            return self.__parent.recv()
        else:
            return 'can not find child.'

    def reborn(self, time=10):
        msg = {'method': self.REBORN, 'arg': time}
        self.__parent.send(msg)
