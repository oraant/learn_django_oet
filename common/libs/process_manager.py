from multiprocessing import Process, Pipe
from threading import Thread, Timer


class ProcessManager:  # change to protect function to avoid children class overwrite it attributes.
    """
    This class will create a child process and do the main jobs, and manage children with father's method.
    This class fit with the situation when a man manager processes with command line.
    Doesn't support multi-concurrence manager operations.

    Attributes:  # todo : complete this.
        __parent (_multiprocessing.Connection): socket connection use to talk with child process.
        __child (_multiprocessing.Connection): socket connection use to talk with parent process.
        __status (str): parent and child process's status
        __suspend_start_timer (threading.Timer): a timer to suspend start action.
        __process (multiprocessing.process.Process):  child process.
    """

    # actions and status for child's job

    START_CHILD_JOB, STOP_CHILD_JOB, CHECK_CHILD_JOB = 'START_CHILD_JOB', 'STOP_CHILD_JOB', 'CHECK_CHILD_JOB'
    RESTART_CHILD_JOB, REBORN_CHILD_JOB = 'RESTART_CHILD_JOB', 'REBORN_CHILD_JOB'

    CHILD_JOB_STARTING, CHILD_JOB_RUNNING = 'CHILD_JOB_STARTING', 'CHILD_JOB_RUNNING'
    CHILD_JOB_STOPPING, CHILD_JOB_STOPPED = 'CHILD_JOB_STOPPING', 'CHILD_JOB_STOPPED'
    CHILD_JOB_SUSPENDED = 'CHILD_JOB_SUSPENDED'

    # actions and status for child's process

    CLOSE_CHILD_PROCESS = 'CLOSE_CHILD_PROCESS'

    PARENT_PROCESS_INITIAL = 'PARENT_PROCESS_INITIAL'
    CHILD_PROCESS_OPENED, CHILD_PROCESS_CLOSED = 'CHILD_PROCESS_OPENED', 'CHILD_PROCESS_CLOSED'

    def __init__(self):
        """
        Init variables for instance.
        """
        self.__parent, self.__child = Pipe()

        self.__status = self.PARENT_PROCESS_INITIAL  # use in father and child process with different value.
        self.__suspend_start_timer = None

        self.__process = Process(target=self.__listen)

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

    @__premise([PARENT_PROCESS_INITIAL])  # todo : should be open when closed. And add unit test.
    def open(self):
        self.__status = self.CHILD_PROCESS_OPENED
        self.__process.start()
        return 'child process generated'

    @__premise([CHILD_PROCESS_OPENED])
    def close(self):
        self.__status = self.CHILD_PROCESS_CLOSED
        self.__parent.send({'method': self.CLOSE_CHILD_PROCESS})
        return self.__parent.recv()

    @__premise([CHILD_PROCESS_OPENED])
    def start(self):
        self.__parent.send({'method': self.START_CHILD_JOB})
        return self.__parent.recv()

    @__premise([CHILD_PROCESS_OPENED])
    def stop(self):  # can't start after stopped
        self.__parent.send({'method': self.STOP_CHILD_JOB})
        return self.__parent.recv()

    @__premise([CHILD_PROCESS_OPENED])
    def restart(self):
        self.__parent.send({'method': self.RESTART_CHILD_JOB})
        return self.__parent.recv()

    @__premise([CHILD_PROCESS_OPENED])
    def reborn(self, time=10):
        self.__parent.send({'method': self.REBORN_CHILD_JOB, 'arg': time})
        return self.__parent.recv()

    @__premise([CHILD_PROCESS_OPENED, CHILD_PROCESS_CLOSED])
    def check(self):
        self.__parent.send({'method': self.CHECK_CHILD_JOB})
        if self.__parent.poll(0.1):
            return self.__parent.recv()
        else:
            return 'can not find child.'

    # method for child process.

    def __listen(self):  # the main thread running in child process.

        operations = {
            self.START_CHILD_JOB: self.__start,
            self.STOP_CHILD_JOB: self.__stop,
            self.RESTART_CHILD_JOB: self.__restart,
            self.CHECK_CHILD_JOB: self.__check,
            self.REBORN_CHILD_JOB: self.__reborn,
            self.CLOSE_CHILD_PROCESS: self.__close,
        }

        # call methods with args or not, and respond methods' result.
        while self.__status != self.CHILD_PROCESS_CLOSED:
            msg = self.__child.recv()  # blocking and wait.
            if msg['method'] in operations.keys():
                if 'arg' in msg.keys():
                    result = operations.get(msg['method'])(msg['arg'])
                else:
                    result = operations.get(msg['method'])()
            else:
                result = "Invalid Command."
            self.__child.send(result)

    @__premise([CHILD_JOB_STOPPED])
    def __close(self):
        self.__status = self.CHILD_PROCESS_CLOSED
        return 'child process is closed.'

    @__premise([CHILD_PROCESS_OPENED, CHILD_JOB_STOPPED, CHILD_JOB_SUSPENDED])
    def __start(self, block=False):  # todo : optimize with map method, maybe.
        """
        Starting child process's main job by calling _start().
        Args:
            block (bool): when starting main job, just call _start() and wait for complete, or do it in a new thread.
        Returns:
            str: explain how's it going.
        """

        self.__status = self.CHILD_JOB_STARTING

        def _start_handler():
            self._start()
            self.__status = self.CHILD_JOB_RUNNING

        if block:
            _start_handler()
            msg = "Child process's job started"
        else:
            Thread(target=_start_handler, name="calling start").start()
            msg = "Trying to start child process's job"

        return msg

    @__premise([CHILD_JOB_RUNNING])
    def __stop(self, block=False):  # todo : maybe join is better when blocking code.
        """
        Stopping child process's main job by calling _stop().
        Args:
            block (bool): when stopping main job, just call _stop() and wait for complete, or do it in a new thread.
        Returns:
            str: explain how's it going.
        """

        self.__status = self.CHILD_JOB_STOPPING

        def _stop_handler():
            self._stop()
            self.__status = self.CHILD_JOB_STOPPED

        if block:
            _stop_handler()
            msg = "Child process's job stopped."
        else:
            Thread(target=_stop_handler, name="calling stop").start()
            msg = "Trying to stop Child process's job."

        return msg

    @__premise([CHILD_JOB_RUNNING, CHILD_JOB_STOPPED])
    def __restart(self):
        """
        Restart the child process's main job by calling _stop(True) and _start().
        Returns:
            str: explain how's it going.
        """

        def _restart_handler():  # will block for a will
            self.__stop(True)
            self.__start()

        if self.__status == self.CHILD_JOB_RUNNING:  # restart job
            Thread(target=_restart_handler, name="calling restart").start()
            msg = "Trying to restart Child process's job."
        else:  # start job
            self.__start()
            msg = "Child process's job is not running.Trying to start it."

        return msg

    @__premise([CHILD_JOB_RUNNING, CHILD_JOB_STOPPED, CHILD_JOB_SUSPENDED])
    def __reborn(self, time):
        """
        Reborn the child process's main job.

        Different from restart() is that this method will stop the main job immediately, but start it after a long time.
        The waiting status is called 'CHILD_JOB_SUSPENDED', and the start action is called 'suspend'.
        When child's process is 'suspended', calling __reborn will cancel the wait action.

        Args:
            time (int): time to wait when suspend the start action.

        Returns:
            str: explain how's it going.
        """

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
            self.__status = self.CHILD_JOB_SUSPENDED

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
            self.CHILD_JOB_RUNNING: _reborn,
            self.CHILD_JOB_STOPPED: _suspend,
            self.CHILD_JOB_SUSPENDED: _cancel,
        }

        msg = operations.get(self.__status)()
        return msg

    def __check(self):
        """
        Check child process's status
        Returns:
            str: the status of child's process
        """
        msg = "child process's job status is %s" % self.__status
        return msg

    # method for subclass

    def _start(self):
        """Children Class's code here, Make sure job is running and can be stop immediately."""
        pass

    def _stop(self):
        """Children Class's code here, Make sure all job done and can be start immediately."""
        pass

    def _run(self):
        """Children Class's code here, do the main job. This is optional."""
        pass
