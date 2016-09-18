from django.test import TestCase
from common.libs.process_manager import ProcessManager
from time import sleep
from threading import Thread


# todo : some open should be closed after raise exceptions like asserts
# todo : abnormal cases


class MyProcessManager(ProcessManager):
    def __init__(self):
        self.run = True
        ProcessManager.__init__(self)

    def _start(self):
        self.run = True
        Thread(target=self._run).start()
        print '>>>'

    def _run(self):
        while self.run:
            sleep(2)
            print "-> -> ->"

    def _stop(self):
        self.run = False
        sleep(2.2)
        print '<<<'


# from apscheduler.schedulers.background import BackgroundScheduler as Scheduler
# from apscheduler.events import EVENT_JOB_ERROR
# from datetime import datetime
# from apscheduler.executors.pool import ThreadPoolExecutor
# import threading
#
# class ScheduleJobs(ProcessManager):
#
#     def __init__(self, name):
#         self.name = name
#         ProcessManager.__init__(self)
#
#     def _set_logger(self):
#         import logging
#         logging.basicConfig()
#         pass
#
#     def _output(self, msg="hello"):
#         print msg, self.name
#         raise KeyError('haha')
#
#     def _exc_handler(self, event):
#         if not event.exception:
#             return
#
#         try:
#             raise event.exception
#         except Exception as e:
#             threading.current_thread().name = 'listener'
#             print "I got Error! It's ", type(e), e
#             print "restarting it self for 5s"
#             self.gap_time = 5
#             self.restart()
#             print "restart done"
#             sleep(3)
#             print self.status()
#
#     def _run(self):
#         self._set_logger()
#         executors = {'default': ThreadPoolExecutor(3)}
#         self.scheduler = Scheduler(executors=executors)
#         self.scheduler.add_job(self._output, 'interval', seconds=2, next_run_time=datetime.now())
#         self.scheduler.add_listener(self._exc_handler, EVENT_JOB_ERROR)
#         self.scheduler.start()
#
#     def _terminate(self):
#         self.scheduler.shutdown(wait=False)


class ProcessManagerTest(TestCase):
    def setUp(self):
        self.mypm = MyProcessManager()

    def test_function(self):
        # open
        print '------ open'
        result = self.mypm.status()
        print result
        self.assertEqual(result,
                         "Status PARENT_PROCESS_INITIAL is not in ['CHILD_PROCESS_OPENED', 'CHILD_PROCESS_CLOSED'].")

        result = self.mypm.open()
        print result
        self.assertEqual(result, "child process generated")

        sleep(1)

        # start
        print '------ start'
        result = self.mypm.start()
        print result
        self.assertEqual(result, "Trying to start child process's job")

        sleep(1)

        result = self.mypm.status()
        print result
        self.assertEqual(result, "child process's job status is CHILD_JOB_RUNNING")

        sleep(1)

        # restart
        print '------ restart'
        result = self.mypm.restart()
        print result
        self.assertEqual(result, "Trying to restart Child process's job.")

        sleep(1)

        result = self.mypm.status()
        print result
        self.assertEqual(result, "child process's job status is CHILD_JOB_STOPPING")

        sleep(3)

        result = self.mypm.status()
        print result
        self.assertEqual(result, "child process's job status is CHILD_JOB_RUNNING")
        sleep(1)

        # reborn
        print '------ reborn'
        result = self.mypm.reborn(3)
        print result
        self.assertEqual(result, "Trying to reborn Child process's job.")

        sleep(1)

        result = self.mypm.status()
        print result
        self.assertEqual(result, "child process's job status is CHILD_JOB_STOPPING")

        sleep(3)

        result = self.mypm.status()
        print result
        self.assertEqual(result, "child process's job status is CHILD_JOB_SUSPENDED")

        sleep(5)

        result = self.mypm.status()
        print result
        self.assertEqual(result, "child process's job status is CHILD_JOB_RUNNING")

        sleep(1)

        # stop
        print '------ stop'
        result = self.mypm.stop()
        print result
        self.assertEqual(result, "Trying to stop Child process's job.")

        sleep(1)

        result = self.mypm.status()
        print result
        self.assertEqual(result, "child process's job status is CHILD_JOB_STOPPING")

        sleep(2)

        result = self.mypm.status()
        print result
        self.assertEqual(result, "child process's job status is CHILD_JOB_STOPPED")

        # close
        print '------ close'
        result = self.mypm.close()
        print result
        self.assertEqual(result, "child process is closed.")

        sleep(1)

        result = self.mypm.status()
        print result
        self.assertEqual(result, "can not find child.")

        sleep(1)

        result = self.mypm.open()
        print result
        self.assertEqual(result, "Status CHILD_PROCESS_CLOSED is not in ['PARENT_PROCESS_INITIAL'].")
