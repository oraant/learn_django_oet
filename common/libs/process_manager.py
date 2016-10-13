from multiprocessing import Process, Pipe
from threading import Thread, Timer
from logging import getLogger


class ProcessManager:  # change to protect function to avoid children class overwrite it attributes.
    """
    This class will create a child process and do the main jobs, and manage children with father's method.
    This class fit with the situation when a man manager processes with command line.
    Doesn't support multi-concurrence manage operations.

    Attributes:
        __parent (_multiprocessing.Connection): socket connection use to talk with child process.
        __child (_multiprocessing.Connection): socket connection use to talk with parent process.
        filenos (list[int]): file descriptors list, keep pipe open when turn to daemon, set by server.

        logger (logging.Logger): better be overwrite by child class.

        __status (str): parent and child process's status
        __suspend_start_timer (threading.Timer): a timer to suspend start action.

        cls.START_CHILD_JOB (str): request for start child process's job.
        cls.STOP_CHILD_JOB (str): request for stop child process's job.
        cls.CHECK_CHILD_JOB (str): request for check child process's job.
        cls.RESTART_CHILD_JOB (str): request for restart child process's job.
        cls.REBORN_CHILD_JOB (str): request for reborn child process's job.

        cls.CHILD_JOB_STARTING (str): child process's job's status which means it's trying to start
        cls.CHILD_JOB_RUNNING (str): child process's job's status which means it's running
        cls.CHILD_JOB_STOPPING (str): child process's job's status which means it's trying to stop
        cls.CHILD_JOB_STOPPED (str): child process's job's status which means it's stopped
        cls.CHILD_JOB_SUSPENDED (str): child process's job's status which means it's hanging for reborn

        cls.CLOSE_CHILD_PROCESS (str): request for close child's process

        cls.PARENT_PROCESS_INITIAL (str): child process's stautus which means it's not been created yet.
        cls.CHILD_PROCESS_OPENED (str): child process's stautus which means it's opened
        cls.CHILD_PROCESS_CLOSED (str): child process's stautus which means it's closed
    """

    # actions for child's job
    START_CHILD_JOB = 'START_CHILD_JOB'
    STOP_CHILD_JOB = 'STOP_CHILD_JOB'
    CHECK_CHILD_JOB = 'CHECK_CHILD_JOB'
    RESTART_CHILD_JOB = 'RESTART_CHILD_JOB'
    REBORN_CHILD_JOB = 'REBORN_CHILD_JOB'

    # status for child's job
    CHILD_JOB_STARTING = 'CHILD_JOB_STARTING'
    CHILD_JOB_RUNNING = 'CHILD_JOB_RUNNING'
    CHILD_JOB_STOPPING = 'CHILD_JOB_STOPPING'
    CHILD_JOB_STOPPED = 'CHILD_JOB_STOPPED'
    CHILD_JOB_SUSPENDED = 'CHILD_JOB_SUSPENDED'

    # actions for child's process
    CLOSE_CHILD_PROCESS = 'CLOSE_CHILD_PROCESS'

    # status for child's process
    PARENT_PROCESS_INITIAL = 'PARENT_PROCESS_INITIAL'
    CHILD_PROCESS_OPENED = 'CHILD_PROCESS_OPENED'
    CHILD_PROCESS_CLOSED = 'CHILD_PROCESS_CLOSED'

    def __init__(self):
        self.__parent, self.__child = Pipe()
        self.filenos = [self.__parent.fileno(), self.__child.fileno()]

        self.logger = getLogger()

        self.__status = self.PARENT_PROCESS_INITIAL  # use in father and child process with different value.
        self.__suspend_start_timer = None

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
        """Create and start child's process."""
        self.logger.info('opening child')
        self.__status = self.CHILD_PROCESS_OPENED
        process = Process(target=self.__listen)
        process.start()
        return 'child process generated'

    @__premise([CHILD_PROCESS_OPENED])
    def close(self):
        """Send request to stop child's process."""
        self.logger.info('closing child')
        self.__status = self.CHILD_PROCESS_CLOSED
        self.__parent.send({'method': self.CLOSE_CHILD_PROCESS})
        return self.__parent.recv()

    @__premise([CHILD_PROCESS_OPENED])
    def start(self):
        """Send request to start child's job."""
        self.logger.info('starting child')
        self.__parent.send({'method': self.START_CHILD_JOB})
        return self.__parent.recv()

    @__premise([CHILD_PROCESS_OPENED])
    def stop(self):  # can't start after stopped  # what's this for?
        """Send request to stop child's job."""
        self.logger.info('stopping child')
        self.__parent.send({'method': self.STOP_CHILD_JOB})
        return self.__parent.recv()

    @__premise([CHILD_PROCESS_OPENED])
    def restart(self):
        """Send request to restart child's job."""
        self.logger.info('restarting child')
        self.__parent.send({'method': self.RESTART_CHILD_JOB})
        return self.__parent.recv()

    @__premise([CHILD_PROCESS_OPENED])
    def reborn(self, time=10):
        """Send request to reborn child's job."""
        self.logger.info('reborning child')
        self.__parent.send({'method': self.REBORN_CHILD_JOB, 'arg': time})
        return self.__parent.recv()

    @__premise([CHILD_PROCESS_OPENED, CHILD_PROCESS_CLOSED])
    def check(self):
        """Send request to check child's job."""
        self.logger.info('checking status of child')
        self.__parent.send({'method': self.CHECK_CHILD_JOB})

        if self.__parent.poll(0.1):
            received = self.__parent.recv()
            self.logger.info('received response when check child: %s' % received)
            return received
        else:
            self.logger.info('can\'t receive response when check child')
            return 'can not find child.'

    # method for child process.

    def __listen(self):  # the main thread running in child process.

        self.logger.debug('start listening')

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
            self.logger.debug('keep listening')

            msg = self.__child.recv()  # blocking and wait.
            self.logger.debug('received msg: %s' % msg)

            if msg['method'] in operations.keys():
                if 'arg' in msg.keys():
                    result = operations.get(msg['method'])(msg['arg'])
                else:
                    result = operations.get(msg['method'])()
            else:
                result = "Invalid Command."

            self.logger.debug('child process sending response: %s' % result)
            self.__child.send(result)

    @__premise([CHILD_JOB_STOPPED])
    def __close(self):
        self.logger.debug('child closing')
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

        self.logger.debug('child starting')
        self.__status = self.CHILD_JOB_STARTING

        # try to call _start()
        def _start_handler():
            try:
                self._start()
            except Exception as e:
                self.logger.error("Child process start failed: %s. Type is: %s" % (e, type(e)))
                self.__status = self.CHILD_PROCESS_OPENED
            else:
                self.logger.debug("Child process start successfully")
                self.__status = self.CHILD_JOB_RUNNING

        # call child's _start in or not in thread.
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

        self.logger.debug('child stopping')

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

        self.logger.debug('child restarting')

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

        self.logger.debug('child reborning')

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
                self.logger.error("Internal Error: suspending canceling, but instance variable is None.")
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
        self.logger.debug('child checking')
        msg = "child process's job status is %s" % self.__status
        return msg

    # method for subclass

    def _start(self):
        """Children Class's code here, Make sure job is running and can be stop immediately."""
        pass

    def _stop(self):
        """Children Class's code here, Make sure all job done and can be start immediately."""
        pass
