# coding:utf-8

from django.core.management.base import BaseCommand, CommandError
from puller.models import GlobalConfigs
from puller.libs import verify,pull,cache # todo: change to cacher and puller,now it's conflict with puller app

import daemon
import multiprocessing as multi
#from apscheduler.schedulers.background import BackgroundScheduler as Scheduler


import os,sys,time
import logging,warnings

# complete this with daemon and socket server.

class Command(BaseCommand):
    help = 'Start Pull datas from target oracle instances.'

    def call(self,dbconfig):
        try:
            proxy = Proxy(dbconfig)
            process = multi.Process(target=proxy.schedule())
            process.start()
        except Exception,e:
            print "===",Exception,e
            return

    def handle(self, *args, **options):
        logging.basicConfig()
        warnings.filterwarnings("ignore")

        from puller.models import DBConfigs
        dbconfigs=DBConfigs.objects.all()
        map(self.call,dbconfigs)
        print '=== handle done'
