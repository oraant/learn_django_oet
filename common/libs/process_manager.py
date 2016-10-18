from multiprocessing import Process, Pipe
from logging import getLogger
from time import sleep
from functools import partial

# actions to send
RUN_CHILD_JOB = 'RUN_CHILD_JOB'
END_CHILD_JOB = 'END_CHILD_JOB'
PING_CHILD_JOB = 'PING_CHILD_JOB'
CLOSE_CHILD_PROCESS = 'CLOSE_CHILD_PROCESS'
PING_CHILD_PROCESS = 'PING_CHILD_PROCESS'


class ProcessManager:
    """
    Attributes:
        sender (PipeSender):
        listener (PipeListener):
        opened (bool):
        process (Process):
    """

    def __init__(self, job, logger=getLogger(), check_time=100):  # todo : complete comments
        """
        Args:
            job (MainJob):
            logger (logging.Logger):
            check_time (int):
        """

        self.job = job
        self.logger = logger
        self.check_time = check_time

        self.opened = False

    # interface functions to call by others

    def start(self):
        return self.__run()

    def stop(self):
        return self.__close()

    def ping(self):
        return self.__ping()

    def call(self, method):
        """
        Call method via string request.
        Args:
            method (str):
        Returns:
            bool:
            str:
        """
        operations = {"start": self.start, "stop": self.stop, "ping": self.ping}
        if method not in operations.keys():
            return False, 'Unknown command.'
        return operations.get(method)()

    # internal functions to handle logic

    def __open(self):
        if self.opened:  # case1: has already opened
            return False, 'Has already opened'
        else:  # case2: never opened

            parent_pipe, child_pipe = Pipe()
            self.sender = PipeSender(parent_pipe, child_pipe, self.logger)
            self.listener = PipeListener(child_pipe, self.job, self.logger)
            self.process = Process(target=self.listener.listen)

            self.opened = True
            self.process.start()
            return True, 'Process opened.'

    def __close(self):
        if not self.opened:  # case1: process closed or never opened
            return False, 'already closed or never opened'

        if self.sender.ping_job()[0]:  # case2: if job is running, close it first
            result, msg = self.sender.end_job()
            if not result:
                return result, msg  # result1: close job failed

        if self.sender.ping_process()[0]:  # case3: if process is running, close it
            result, msg = self.sender.close_process()
            if not result:
                return result, msg  # result2: close process failed

        self.process.join()
        self.opened = False
        return True, 'job stopped and process closed.'

    def __run(self):
        if not self.opened:  # case1: if process didn't open, open first.
            self.__open()

        if self.sender.ping_job()[0]:  # case2: process opened but child's job is already running.
            return False, 'job is already running'

        result, msg = self.sender.run_job()  # case3: process opened and child's job is not running
        return result, msg

    def __end(self):
        if not self.opened:  # case1: process didn't open
            return False, 'process did not open'

        if not self.sender.ping_job()[0]:  # case2: process opened but job is not running.
            return False, 'job is not running'

        result, msg = self.sender.end_job()  # case3: process opened and job is running.
        return result, msg

    def __ping(self):
        if not self.opened:  # case1: process didn't open
            return False, 'process did not open'

        if self.sender.ping_job()[0]:  # case2: process opened and job is running.
            return True, 'job is running'

        if self.sender.ping_process()[0]:  # case3: process opened but job is not running.
            return False, 'job is not running'

    def __watch(self):  # todo : do this with a new thread.

        while True:
            sleep(self.check_time)

            if not self.opened:  # case1: process closed or never opened
                continue

            if not self.job.ping():  # case2: process opened and and job is not running
                self.__close()
                self.__run()


class PipeSender:

    def __init__(self, parent_pipe, child_pipe, logger):

        self.parent_pipe = parent_pipe
        self.child_pipe = child_pipe

        self.logger = logger

        self.run_job = partial(self.send, msg=RUN_CHILD_JOB)
        self.end_job = partial(self.send, msg=END_CHILD_JOB)
        self.ping_job = partial(self.send, msg=PING_CHILD_JOB, wait_time=1)
        self.close_process = partial(self.send, msg=CLOSE_CHILD_PROCESS)
        self.ping_process = partial(self.send, msg=PING_CHILD_PROCESS, wait_time=1)

    def send(self, msg, wait_time=None):
        self.logger.debug('[[ ParentPipe ]] >>> ( %s )' % msg)

        self.parent_pipe.send(msg)

        if not wait_time:
            result, msg = self.parent_pipe.recv()
        elif self.parent_pipe.poll(wait_time):
            result, msg = self.parent_pipe.recv()
        else:
            result, msg = False, 'child process has no response.'

        self.logger.debug('[[ ParentPipe ]] <<< ( %s, %s )' % (result, msg))
        return result, msg


class PipeListener:

    def __init__(self, pipe, job, logger):
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

    def listen(self):  # the main thread running in child process.

        while self.keep_listen:
            self.logger.debug('process keep listening')

            msg = self.pipe.recv()  # blocking and wait.
            self.logger.debug('( %s ) >>> [[ Child Pipe ]]' % msg)

            try:
                if msg in self.operations.keys():
                    result, msg = self.operations.get(msg)()
                else:
                    result, msg = False, "Invalid Command."
            except Exception as e:
                self.logger.error(e)

            self.logger.debug('( %s, %s ) <<< [[ Child Pipe ]]' % (result, msg))
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

    def run(self):
        try:
            result, msg = self.job.run()
        except TypeError:
            result, msg = True, 'Job run successfully -- maybe.'
        except Exception as e:
            result, msg = False, 'Unknown Error when ping job, please check log file.'
            self.logger("[%s] - %s" % (type(e), e))

        return result, msg

    def end(self):
        try:
            result, msg = self.job.end()
        except TypeError:
            result, msg = True, 'Job end successfully -- maybe.'
        except Exception as e:
            result, msg = False, 'Unknown Error when ping job, please check log file.'
            self.logger("[%s] - %s" % (type(e), e))
        return result, msg

    def ping_job(self):
        try:
            result, msg = self.job.ping()
        except TypeError:
            result, msg = False, 'can check status of job. job.ping() function did not return right value.'
        except Exception as e:
            result, msg = False, 'Unknown Error when ping job, please check log file.'
            self.logger("[%s] - %s" % (type(e), e))

        return result, msg


class MainJob:

    def __init__(self, logger=getLogger()):
        self.logger = logger

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
        return True, 'job is empty.'
