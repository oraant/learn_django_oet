from multiprocessing import Process, Pipe
from logging import getLogger
from functools import partial
from threading import Thread, Lock, Event

# actions to send
RUN_CHILD_JOB = 'RUN_CHILD_JOB'
END_CHILD_JOB = 'END_CHILD_JOB'
PING_CHILD_JOB = 'PING_CHILD_JOB'
CLOSE_CHILD_PROCESS = 'CLOSE_CHILD_PROCESS'
PING_CHILD_PROCESS = 'PING_CHILD_PROCESS'


class JobManager:
    """
    Manager a job with a new process.

    Notes:
        This will run the job in a new process.
        The manager will check job's status automatically, and try to restart it.

    Attributes:
        opened (bool): dose the job successfully started or successfully stopped.
        mutex (thread.lock): make sure call start, stop, ping and __watch method once at same time.
        closed (Event): when closing job successfully, stop the __watch thread.

        sender (PipeSender): send msg to child process's pipe listener.
        listener (PipeListener): run a child process and listen pipe msg.
        process (Process): child process, declare it as instance variable to close it clearly with join() method.

    """

    def __init__(self, job, logger_name, check_time=3600):  # todo : complete comments
        """
        Instance of job manager

        Args:
            logger_name (str): name of the logger, make this individual when you have multi manager.
            job (MainJob): the job to manage.
            check_time (int): interval time to check job's status, unit is seconds.
        """

        self.logger = getLogger(logger_name)
        self.job = job
        self.check_time = check_time

        self.opened = False
        self.mutex = Lock()
        self.closed = Event()

    # interface functions to call by others

    def start(self):
        """
        Try to start job.

        Notes:
            This need a mutex lock, so it may hang for a while if another action is busying.

        Returns:
            bool: result of this action, True means successful, and False means failed.
            str: message of the result
        """
        if self.mutex.acquire(True):
            self.logger.info('starting job.')
            result, msg = self.__start()
            self.mutex.release()
            return result, msg

    def stop(self):
        """
        Try to stop job.

        Notes:
            This need a mutex lock, so it may hang for a while if another action is busying.

        Returns:
            bool: result of this action, True means successful, and False means failed.
            str: message of the result
        """
        if self.mutex.acquire(True):
            self.logger.info('stopping job.')
            result, msg = self.__stop()
            self.mutex.release()
            return result, msg

    def ping(self):
        """
        Try to check job's status

        Notes:
            This need a mutex lock, so it may hang for a while if another action is busying.

        Returns:
            bool: if the job is running. True means running.
            str: message of the result
        """
        if self.mutex.acquire(True):
            self.logger.info('checking job.')
            result, msg = self.__ping()
            self.mutex.release()
            return result, msg

    def call(self, method):
        """
        Call method via string request.

        Args:
            method (str): which method you want to call.

        Returns:
            bool: result of the method
            str: message of the result
        """
        operations = {"start": self.start, "stop": self.stop, "ping": self.ping}
        if method not in operations.keys():
            return False, 'Unknown command.'
        return operations.get(method)()

    # internal functions to handle logic

    def __start(self):
        """
        Try to start job.

        Notes:
            This need a mutex lock, so it may hang for a while if another action is busying.

        Returns:
            bool: result of this action, True means successful, and False means failed.
            str: message of the result
        """

        # job has already started before.
        if self.opened:
            return False, 'Job has started before.'

        # try to open process.
        open_result, open_msg = self.__open()

        # process opened failed.
        if not open_result:
            return open_result, open_msg

        # try to run job.
        run_result, run_msg = self.__run()

        # run job failed.
        if not run_result:

            close_result, close_msg = self.__close()

            if not close_result:  # run job failed, and close process failed.
                return False, 'Run job failed - %s\nClose process failed - %s' % (run_msg, close_msg)
            else:  # run job failed, and close process successfully.
                return run_result, run_msg

        # run job successfully.
        Thread(target=self.__watch).start()
        self.opened = True
        return run_result, run_msg

    def __stop(self):
        """
        Try to stop job.

        Notes:
            This need a mutex lock, so it may hang for a while if another action is busying.

        Returns:
            bool: result of this action, True means successful, and False means failed.
            str: message of the result
        """

        # job is not running.
        if not self.opened:
            return False, 'Job is not running.'

        # if job is running, then stop it first.
        if self.sender.ping_job()[0]:

            end_result, end_msg = self.__end()

            if not end_result:  # job is running but end failed.
                return end_result, end_msg

        # if process is opened, then close it first.
        if self.sender.ping_process()[0]:

            close_result, close_msg = self.__close()

            if not close_result:  # process is opened but close failed.
                return close_result, close_msg
            else:
                self.closed.set()
                self.opened = False
                return True, 'Job stopped successfully'

        # action is opened, but job is ended and process is closed
        return False, 'Logic Error, action is opened, but job is ended and process is closed.'

    def __watch(self):
        """
        Keep check job's status in a new thread.

        Notes:
            If it found job has crushed, then try to restart it.
            If restart job successfully, then will keep watching, if not, it won't watch anymore.
            This need a mutex lock, so it won't execute if another action is busying.
        """

        self.closed.clear()

        while True:

            if self.closed.wait(self.check_time):  # if process closed, end the watch thread.
                break

            if not self.mutex.acquire(False):  # if mutex has been locked, do nothing
                continue

            if self.sender.ping_job()[0]:  # case3: process opened and and job is running
                self.logger.info('check Job every %ds: job is running healthily.' % self.check_time)
                self.mutex.release()
                continue

            self.logger.warn('check Job every %ds: job is not running! Trying rerun job.' % self.check_time)

            close_result, close_msg = self.__close()
            if not close_result:
                self.logger.error("job crushed, and can't stop process: %s. Stop watching." % close_msg)
                self.mutex.release()
                break

            open_result, open_msg = self.__open()
            if not open_result:
                self.logger.error("job crushed, but restart process failed: %s. Stop watching." % open_msg)
                self.mutex.release()
                break

            run_result, run_msg = self.__run()
            if not run_result:
                self.logger.error("job crushed, but restart job failed: %s. Stop watching." % run_msg)
                self.mutex.release()
                break

            self.logger.info('job crushed, but restart it successfully.')
            self.mutex.release()

    # this functions just do one thing and output a result. they don't need to handle the logic between each other.

    def __open(self):
        """
        Try to open process.

        Notes:
            if this function said process is opened, then it is, so this function will confirm it by ping process.

        Returns:
            bool: process opened successfully or not.
            str: message received from child process, or internal error like opened but ping failed.
        """
        # try to open process
        try:
            parent_pipe, child_pipe = Pipe()
            self.sender = PipeSender(parent_pipe, child_pipe, self.logger)
            self.listener = PipeListener(child_pipe, self.job, self.logger)
            self.process = Process(target=self.listener.listen)
            self.process.start()
        except Exception as e:
            self.logger.error("[%s] - %s" % (type(e), e))
            return False, 'Create process failed, please check logfile.'

        # verify open result
        if not self.sender.ping_process()[0]:
            self.logger.error('Process of job opened, but ping failed.')
            return False, 'Process of job opened, but ping failed.'

        # verify passed
        self.logger.info('Process of job opened, and ping passed.')
        return True, 'Process opened.'

    def __close(self):
        """
        Try to close process.

        Notes:
            if this function said process is closed, then it is, so this function will confirm it by ping process.

        Returns:
            bool: process closed successfully or not.
            str: message received from child process, or internal error like closed but can still ping.
        """
        # try to close process
        result, msg = self.sender.close_process()

        if not result:
            self.logger.error('process stop failed.')
            return result, msg

        # verify close result
        if self.sender.ping_process()[0]:
            self.logger.error('process stopped, but still can ping.')
            return False, 'process stopped, but still can ping.'

        # verify passed
        self.process.join()
        self.logger.info('process stopped successfully')
        return result, msg

    def __run(self):
        """
        Try to run job.

        Notes:
            if this function said job is run, then it is, so this function will confirm it by ping job.

        Returns:
            bool: run job successfully or not.
            str: message received from job, or internal error like opened but ping failed.
        """
        # try to run job
        result, msg = self.sender.run_job()

        if not result:
            self.logger.error('run job failed.')
            return result, msg

        # verify run result
        if not self.sender.ping_job()[0]:
            self.logger.error('job has run, but ping failed.')
            return False, 'job has run, but ping failed.'

        # verify passed
        self.logger.info('job has run, and ping passed.')
        return result, msg

    def __end(self):
        """
        Try to end job.

        Notes:
            if this function said job is ended, then it is, so this function will confirm it by ping job.

        Returns:
            bool: end job successfully or not.
            str: message received from job, or internal error like ended but still can ping.
        """
        # try to end job
        result, msg = self.sender.end_job()

        if not result:
            self.logger.error('end job failed.')
            return result, msg

        # verify end result
        if self.sender.ping_job()[0]:
            self.logger.error('job has end, but still can ping.')
            return False, 'job has end, but still can ping.'

        # verify passed
        self.logger.info('job end successfully')
        return result, msg

    def __ping(self):
        """
        Try to check job's status

        Returns:
            bool: if the job is running. True means running.
            str: message of the result
        """
        if not self.opened:  # case1: process didn't open
            return False, 'process did not open'

        if self.sender.ping_job()[0]:  # case2: process opened and job is running.
            return True, 'job is running'

        if self.sender.ping_process()[0]:  # case3: process opened but job is not running.
            return False, 'job is not running'


class PipeSender:
    """
    Send different message from father pipe to child process's pipe listener.
    """

    def __init__(self, parent_pipe, child_pipe, logger):
        """
        Init instance.

        Args:
            parent_pipe (_multiprocessing.Connection): pipe's father port to send msg to child's port.
            child_pipe (_multiprocessing.Connection): pipe's child port to receive msg from father port.
            logger (logging.Logger): logger to log msg.
        """

        self.parent_pipe = parent_pipe
        self.child_pipe = child_pipe
        self.logger = logger

        self.run_job = partial(self.send, msg=RUN_CHILD_JOB)
        self.end_job = partial(self.send, msg=END_CHILD_JOB)
        self.ping_job = partial(self.send, msg=PING_CHILD_JOB, wait_time=3)
        self.close_process = partial(self.send, msg=CLOSE_CHILD_PROCESS)
        self.ping_process = partial(self.send, msg=PING_CHILD_PROCESS, wait_time=1)

    def send(self, msg, wait_time=None):
        """
        Send message from father pipe to child process's pipe listener.

        Args:
            msg (str): message you want to send to child
            wait_time (int): how long to wait if child doesn't response, or response slowly.

        Returns:
            bool: child's response, which means the action is succeed or not. or just can't receive response.
            msg: child's response, talk us what's going on here.
        """
        self.logger.debug('[[ ParentPipe ]] >>> ( %s ) >>> [[ ---------- ]]' % msg)

        self.parent_pipe.send(msg)

        if not wait_time:
            result, msg = self.parent_pipe.recv()
        elif self.parent_pipe.poll(wait_time):
            result, msg = self.parent_pipe.recv()
        else:
            result, msg = False, 'child process has no response.'

        self.logger.debug('[[ ParentPipe ]] <<< ( %s, %s ) <<< [[ ---------- ]]' % (result, msg))
        return result, msg


class PipeListener:
    """
    Run a child process and listen pipe msg, according to string request, call different method to handle job.

    Attributes:
        keep_listen (bool): If this is true, then the process's main thread will keep listen msg from pipe.
        operations (dict{str:function}): dictionary with functions for mapping string to method.
    """

    def __init__(self, pipe, job, logger):
        """
        Init instance.

        Args:
            pipe (_multiprocessing.Connection): pipe's child port to receive msg from father port.
            job (MainJob): the job you want to manage, like run, end and auto restart when it crushed.
            logger (logging.Logger): log messages.
        """
        self.pipe = pipe
        self.job = job
        self.logger = logger

        self.keep_listen = True

        self.operations = {
            RUN_CHILD_JOB: self.run,
            END_CHILD_JOB: self.end,
            PING_CHILD_JOB: self.ping_job,
            CLOSE_CHILD_PROCESS: self.close,
            PING_CHILD_PROCESS: self.ping_process,
        }

    def listen(self):
        """
        The main thread of the child process, receive string msg from pipe, and call the mapping method.

        Returns:

        """

        while self.keep_listen:
            self.logger.debug('process keep listening')

            msg = self.pipe.recv()  # blocking and wait.
            self.logger.debug('[[ ---------- ]] >>> ( %s ) >>> [[ Child Pipe ]]' % msg)

            try:
                if msg in self.operations.keys():
                    result, msg = self.operations.get(msg)()
                else:
                    result, msg = False, "Invalid Command."
            except Exception as e:
                self.logger.error('[%s] - %s' % (type(e), e))

            self.logger.debug('[[ ---------- ]] <<< ( %s, %s ) <<< [[ Child Pipe ]]' % (result, msg))
            self.pipe.send([result, msg])

    # logic method, must return str and handle __status

    def close(self):
        """
        Stop child's process by change status
        Returns:
            str: close successfully or failed.
        """
        self.logger.debug('process closing')
        self.keep_listen = False
        return True, 'child process is closed.'

    def ping_process(self):
        """
        Check child process's job's status
        Returns:
            bool:
        """
        self.logger.debug('process pong')
        return True, 'child process is running.'

    # call job's functions

    def run(self):
        try:
            result, msg = self.job.run()
        except TypeError:
            result, msg = True, 'Job run successfully -- maybe.'
        except Exception as e:
            result, msg = False, 'Unknown Error when run job, please check log file.'
            self.logger.error("[%s] - %s" % (type(e), e))

        return result, msg

    def end(self):
        try:
            result, msg = self.job.end()
        except TypeError:
            result, msg = True, 'Job end successfully -- maybe.'
        except Exception as e:
            result, msg = False, 'Unknown Error when run job, please check log file.'
            self.logger.error("[%s] - %s" % (type(e), e))

        return result, msg

    def ping_job(self):
        try:
            result, msg = self.job.ping()
        except TypeError:
            result, msg = False, 'can check status of job. job.ping() function did not return right value.'
        except Exception as e:
            result, msg = False, 'Unknown Error when ping job, please check log file.'
            self.logger.error("[%s] - %s" % (type(e), e))

        return result, msg


class MainJob:

    def __init__(self, logger_name):
        self.logger = getLogger(logger_name)

    def run(self):
        """
        Notes:
            Start a new thread to run main job.
            Never blocking! Run the thread at background.
        Returns:
            bool: run successful or not
            str:
        """
        self.logger.debug('empty job started')
        return True, 'job is empty.'

    def end(self):
        """
        Notes:
            End the job thread.
            Need blocking! When this method done, make sure all job has stopped.
        Returns:
            bool: terminated successful or not
            str:
        """
        self.logger.debug('empty job stopped')
        return True, 'job is empty.'

    def ping(self):
        """
        Check if child's job is running.
        Returns:
            bool: if child's job is running.
            str:
        """
        self.logger.debug('empty job pong')
        return False, 'job is empty.'
