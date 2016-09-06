from django.test import TestCase
from common.libs.process_manager import ProcessManager
from time import sleep

# todo : some open should be closed after raise exceptions like asserts
# todo : abnormal cases

class MyProcessManager(ProcessManager):

    def __init__(self):
        self.run = True
        ProcessManager.__init__(self)

    def _run(self):
        while self.run:
            sleep(1)
            print "I'm running"

    def _terminate(self):
        self.run = False

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

        self.mypm

    def tearDown(self):
        self.connection.close()
