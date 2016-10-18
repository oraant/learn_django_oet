from multiprocessing import Process, Pipe
from threading import Timer
from logging import getLogger
import traceback
from traceback import format_exc


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
        reborn_time (int): how long to wait when reborn.

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


    def __init__(self):  # todo : better split different method in different class.
        self.__parent, self.__child = Pipe()
        self.filenos = [self.__parent.fileno(), self.__child.fileno()]

        self.logger = getLogger()
        self.reborn_time = 10

        self.__status = self.PARENT_PROCESS_INITIAL  # use in father and child process with different value.

        self.__suspend_start_timer = None

    # decorator for father and child

    def __premise(status):
        def decorator(func):
            def wrapper(self, *args, **kw):
                if self.__status in status:
                    return func(self, *args, **kw)
                else:
                    return "Error 0: Illegal Action:\n  Expect Status is: %s\n  Current Status is: %s." % (status, self.__status)
            return wrapper
        return decorator

    # method for father process.

    @__premise([PARENT_PROCESS_INITIAL])  # todo :should open when closed And add unit test.
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
        self.__parent.send(self.CLOSE_CHILD_PROCESS)
        return self.__parent.recv()

    @__premise([CHILD_PROCESS_OPENED])
    def start(self):
        """Send request to start child's job."""
        self.logger.info('starting child')
        self.__parent.send(self.START_CHILD_JOB)
        return self.__parent.recv()

    @__premise([CHILD_PROCESS_OPENED])
    def stop(self):  # can't start after stopped  # what's this for?
        """Send request to stop child's job."""
        self.logger.info('stopping child')
        self.__parent.send(self.STOP_CHILD_JOB)
        return self.__parent.recv()

    @__premise([CHILD_PROCESS_OPENED])
    def restart(self):
        """Send request to restart child's job."""
        self.logger.info('restarting child')
        self.__parent.send(self.RESTART_CHILD_JOB)
        return self.__parent.recv()

    @__premise([CHILD_PROCESS_OPENED])
    def reborn(self):
        """Send request to reborn child's job."""
        self.logger.info('reborning child')
        self.__parent.send(self.REBORN_CHILD_JOB)
        return self.__parent.recv()

    @__premise([CHILD_PROCESS_OPENED, CHILD_PROCESS_CLOSED])
    def check(self):
        """Send request to check child's job."""
        self.logger.info('checking status of child')
        self.__parent.send(self.CHECK_CHILD_JOB)

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
            self.logger.debug('[[Parent Process]] >>> %s >>> [[Child Process]]' % msg)

            if msg in operations.keys():
                result = operations.get(msg)()
            else:
                result = "Error 1: Invalid Command."

            self.logger.debug('[[Parent Process]] <<< %s <<< [[Child Process]]' % result)
            self.__child.send(result)

    # logic method, must return str and handle __status

    @__premise([CHILD_JOB_STOPPED])
    def __close(self):
        """
        Stop child's process by change status
        Returns:
            str: close successfully or failed.
        """
        self.logger.debug('child closing')

        self.__status = self.CHILD_PROCESS_CLOSED

        return 'child process is closed.'

    @__premise([CHILD_PROCESS_OPENED, CHILD_JOB_STOPPED, CHILD_JOB_SUSPENDED])
    def __start(self):
        """
        Starting child process's main job by calling _start().
        Notes:
            This won't block code.
            This will cancel suspended.
        Returns:
            str: stop successfully or failed.
        """

        self.logger.debug('child starting')

        if self.__status == self.CHILD_JOB_SUSPENDED:
            self.__cancel()

        # try to call _start()
        try:
            self.__status = self.CHILD_JOB_STARTING
            self._start_background_thread()

        except Exception as e:
            self.__status = self.CHILD_PROCESS_OPENED
            self.logger.error("[%s]:%s\n Traceback is: %s" % (e, type(e), format_exc()))
            return "Error 2: Child process start failed, please check logfile."

        else:
            self.__status = self.CHILD_JOB_RUNNING
            return "Child process start successfully"

    @__premise([CHILD_JOB_RUNNING, CHILD_JOB_SUSPENDED])
    def __stop(self):
        """
        Stopping child process's main job by calling _stop().This will block code for a well.
        Notes:
            If it's suspending, then just cancel it.
        Returns:
            str: stop successfully or failed.
        """

        self.logger.debug('child stopping')

        if self.__status == self.CHILD_JOB_SUSPENDED:
            self.__cancel()
            self.__status = self.CHILD_JOB_STOPPED
            return "Child process's job was suspending, now canceled."

        try:
            self.__status = self.CHILD_JOB_STOPPING
            self._stop_with_waiting()
        except Exception as e:
            self.__status = self.CHILD_JOB_RUNNING
            self.logger.error("[%s]:%s\n Traceback is: %s" % (e, type(e), format_exc()))
            return "Error 3: Child process stop failed, please check logfile."
        else:
            self.__status = self.CHILD_JOB_STOPPED
            return "Child process's job stopped."

    @__premise([CHILD_JOB_RUNNING, CHILD_JOB_STOPPED, CHILD_JOB_SUSPENDED])
    def __restart(self):
        """
        Restart the child process's main job by calling _stop(True) and _start().
        Returns:
            str: restart successfully or failed.
        """

        self.logger.debug('child restarting')

        if self.__status == self.CHILD_JOB_RUNNING:  # restart job
            self.__stop()
        self.__start()

        return "Child process's job is not running.Trying to start it."

    @__premise([CHILD_JOB_RUNNING, CHILD_JOB_STOPPED, CHILD_JOB_SUSPENDED])
    def __reborn(self):
        """
        Reborn the child process's main job.
        Notes:
            This stop child's job if it's running
        Returns:
            str: reborn successfully or failed.
        """

        self.logger.debug('child reborning')

        if self.__status == self.CHILD_JOB_RUNNING:
            self.__stop()

        self.__suspend()
        self.__status = self.CHILD_JOB_SUSPENDED

        return "Child job suspending for start"

    # basic method for logic method, des not return things or handle status.

    def __suspend(self):
        """
        Wait time seconds and call __start()
        Notes:
            if there have one before, then cancel it first.
        Args:
            time: how many seconds to wait.
        """

        if self.__suspend_start_timer:
            self.__suspend_start_timer.cancel()

        self.logger.debug("child suspending")
        self.__suspend_start_timer = Timer(self.reborn_time, self.__start)
        self.__suspend_start_timer.start()
        self.logger.debug("child suspended")

    def __cancel(self):
        """Cancel the suspend timer."""

        self.logger.debug("child canceling suspend")
        self.__suspend_start_timer.cancel()
        self.__suspend_start_timer = None

    def __check(self):
        """
        Check child process's status
        Returns:
            str: the status of child's process
        """
        self.logger.debug('child checking')
        msg = "Child process's job status is %s. " % self.__status
        return msg

    # method for subclass

    def _start_background_thread(self):
        """Children Class's code here, Make sure do works in background thread."""
        pass

    def _stop_with_waiting(self):
        """Children Class's code here, Make sure when this method done, works are done."""
        pass
