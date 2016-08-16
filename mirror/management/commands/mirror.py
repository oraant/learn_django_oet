# coding:utf-8

from django.core.management.base import BaseCommand, CommandError
from puller.models import GlobalConfigs
from puller.libs import verify,pull,cache # todo: change to cacher and puller,now it's conflict with puller app

import daemon
import multiprocessing as multi
#from apscheduler.schedulers.background import BackgroundScheduler as Scheduler
from apscheduler.schedulers.blocking import BlockingScheduler as Scheduler

import os,sys,time
import logging,warnings

class Proxy:
    def __init__(self,dbconfig):
        self.dbconfig=dbconfig

        exec("from puller.models import "+dbconfig.tables)
        self.tables = eval(dbconfig.tables).objects.all()
        map(self._format,self.tables)

        self.cacher=cache.Cacher(dbconfig)
        self.puller=pull.Puller(dbconfig)
        self.verify=verify.Verify()

    def _format(self,table):
        '''format table sqls,replace <TABLE_NAME>'''
        table.name = self.dbconfig.name + '_' + table.name
        table.create = table.create.replace("<TABLE_NAME>",table.name)
        table.drop = table.drop.replace("<TABLE_NAME>",table.name)
        table.insert = table.insert.replace("<TABLE_NAME>",table.name)
        table.delete = table.delete.replace("<TABLE_NAME>",table.name)

    def _main(self,table):
        '''pull and cache,record in redis,and write logs'''

        try:
            datas = self.puller.pull(table)
        except Exception,e:
            print Exception,e
            return

        try:
            self.cacher.cache(table,datas)
        except Exception,e:
            print Exception,e
            return

        try:
            self.verify.record(table.name)
        except Exception,e:
            print Exception,e
            return

    def schedule(self):
        '''schedule jobs for every table'''
        scheduler = Scheduler()
        for table in self.tables:
            print 'scheduler adding'
            scheduler.add_job(self._main, 'interval',args=(table,), seconds=table.period)
            print 'scheduler added'

        try:
            scheduler.start()
        except Exception,e:
            print '===',Exception,e
            print '=== an error occured,outing'
        except KeyboardInterrupt,e:
            print '===',KeyboardInterrupt,e
            print '=== you want to stop,outing'
        finally:
            self.cacher.close()
            self.puller.close()

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
