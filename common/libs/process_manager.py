from multiprocessing import Process, Pipe
from threading import Thread, Timer


class ProcessManager:  # change to protect function to avoid children class overwrite it attributes.
    """
    This class will create a child process and do the main jobs, and manage children with father's method.
    This class fit with the situation when a man manager processes with command line.
    Doesn't support multi-concurrence manager operations.

    Attributes:  # todo : complete this.
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

    START, STOP, STATUS, RESTART, REBORN, CLOSE = 'START', 'STOP', 'STATUS', 'RESTART', 'REBORN', 'CLOSE'
    STARTING, RUNNING, STOPPING, STOPPED, SUSPENDED = 'STARTING', 'RUNNING', 'STOPPING', 'STOPPED', 'SUSPENDED'
    INITIAL, OPENED, CLOSED = 'INITIAL', 'OPENED', 'CLOSED'

    # method for subclass

    def __init__(self):  # todo : open,close,status, start,stop,restart, dormant,wake,reborn
        """
        Must at end, because it will block child's code, and wait for pipe msg.
        Attributes

        """
        self.__parent, self.__child = Pipe()

        self.__status = self.INITIAL  # use in father and child process with different value.
        self.__suspend_start_timer = None

        self.__process = Process(target=self.__listen)

    def _start(self):
        """Your code here, Make sure job is running and can be stop immediately."""
        pass

    def _stop(self):
        """Your code here, Make sure all job done and can be start immediately."""
        pass

    def _run(self):
        """Your code here, do the main job."""
        pass

    # decorator for father and child

    def __premise(status):
        def decorator(func):
            def wrapper(self, *args, **kw):
                if self.__status in status:
                    return func(self, *args, **kw)
                else:
                    return "Status %s is not in %s." % (self.__status, str(status))
            return wrapper
        return decorator

    # method for father process.

    @__premise([INITIAL])  # todo : should be open when closed. And add unit test.
    def open(self):
        self.__status = self.OPENED
        self.__process.start()
        return 'child process generated'

    @__premise([OPENED])
    def close(self):
        self.__status = self.CLOSED
        self.__parent.send({'method': self.CLOSE})
        return self.__parent.recv()

    @__premise([OPENED])
    def start(self):
        self.__parent.send({'method': self.START})
        return self.__parent.recv()

    @__premise([OPENED])
    def stop(self):  # can't start after stopped
        self.__parent.send({'method': self.STOP})
        return self.__parent.recv()

    @__premise([OPENED])
    def restart(self):
        self.__parent.send({'method': self.RESTART})
        return self.__parent.recv()

    @__premise([OPENED])
    def reborn(self, time=10):
        self.__parent.send({'method': self.REBORN, 'arg': time})
        return self.__parent.recv()

    @__premise([OPENED, CLOSED])
    def status(self):
        self.__parent.send({'method': self.STATUS})
        if self.__parent.poll(0.1):
            return self.__parent.recv()
        else:
            return 'can not find child.'

    # method for child process.

    def __listen(self):  # the main thread running in child process.

        operations = {
            self.START: self.__start,
            self.STOP: self.__stop,
            self.RESTART: self.__restart,
            self.STATUS: self.__check,
            self.REBORN: self.__reborn,
            self.CLOSE: self.__close,
        }

        while self.__status != self.CLOSED:
            msg = self.__child.recv()  # blocking and wait.
            if msg['method'] in operations.keys():
                if 'arg' in msg.keys():
                    result = operations.get(msg['method'])(msg['arg'])
                else:
                    result = operations.get(msg['method'])()
            else:
                result = "Invalid Command."
            self.__child.send(result)

    @__premise([STOPPED])
    def __close(self):
        self.__status = self.CLOSED
        return 'child process is closed.'

    @__premise([OPENED, STOPPED, SUSPENDED])
    def __start(self, block=False):  # todo : optimize with map method, maybe.
        """
        Starting child process's main job by call it's _run() in a new thread.
        Args:
            block (bool): block or not.

        Returns:
            str: explain how's it going.
        """

        self.__status = self.STARTING

        def _start_handler():
            self._start()
            self.__status = self.RUNNING

        if block:
            _start_handler()
            msg = "Child process's job started"
        else:
            Thread(target=_start_handler, name="calling start").start()
            msg = "Trying to start child process's job"

        return msg

    @__premise([RUNNING])
    def __stop(self, block=False):  # todo : maybe join is better when blocking code.
        """
        Stop child process's main job by call it's _terminate() in a new non-daemon thread.
        Stop child process's listener by change the self.listen variable after child's main job terminated.
        """

        self.__status = self.STOPPING

        def _stop_handler():
            self._stop()
            self.__status = self.STOPPED

        if block:
            _stop_handler()
            msg = "Child process's job stopped."
        else:
            Thread(target=_stop_handler, name="calling stop").start()
            msg = "Trying to stop Child process's job."

        return msg

    @__premise([RUNNING, STOPPED])
    def __restart(self):
        """
        Restart the child process.
        Note that self.listen and self.running changed to False first, then changed to True before listener stop.
        """

        def _restart_handler():  # will block for a will
            self.__stop(True)
            self.__start()

        if self.__status == self.RUNNING:  # restart job
            Thread(target=_restart_handler, name="calling restart").start()
            msg = "Trying to restart Child process's job."
        else:  # start job
            self.__start()
            msg = "Child process's job is not running.Trying to start it."

        return msg

    @__premise([RUNNING, STOPPED, SUSPENDED])
    def __reborn(self, time):

        # todo : create a timer(or wait event thread) at first time, close it at next time.

        def _suspend():
            if self.__suspend_start_timer:  # todo : can be removed after test.
                print "internal error: suspending start, but instance variable is busy."  # todo : a log is better.
                return

            def _suspend_handler():
                self.__start()
                self.__suspend_start_timer = None

            t = Timer(time, _suspend_handler)
            self.__suspend_start_timer = t
            t.start()
            self.__status = self.SUSPENDED

            return "Child process's job is not running.Trying to reborn it."

        def _reborn():  # block for a while

            def _reborn_handler():
                self.__stop(True)
                _suspend()

            Thread(target=_reborn_handler).start()
            return "Trying to reborn Child process's job."

        def _cancel():
            if not self.__suspend_start_timer:
                print "internal error: suspending canceling, but instance variable is None."  # todo : a log is better.
                return

            self.__suspend_start_timer.cancel()
            self.__suspend_start_timer = None
            return "Canceled suspend start for child process's job."

        operations = {
            self.RUNNING: _reborn,
            self.STOPPED: _suspend,
            self.SUSPENDED: _cancel,
        }

        msg = operations.get(self.__status)()
        return msg

    def __check(self):
        msg = "child process's job status is %s" % self.__status
        return msg
