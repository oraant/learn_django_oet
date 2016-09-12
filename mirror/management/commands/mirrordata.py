# coding:utf-8

from django.core.management.base import BaseCommand, CommandError
from mirror.libs.proxy import Proxy
import daemon
import multiprocessing as multi
from mirror.models import OracleTarget
import os,sys,time
import logging,warnings

# complete this with daemon and socket server.

class Command(BaseCommand):

#    def call(self,dbconfig):
#        try:
#            proxy = Proxy(dbconfig)
#            process = multi.Process(target=proxy.schedule())
#            process.start()
#        except Exception,e:
#            print "===",Exception,e
#            return
#
#    def handle(self, *args, **options):
#        logging.basicConfig()
#        warnings.filterwarnings("ignore")
#
#        from puller.models import DBConfigs
#        dbconfigs=DBConfigs.objects.all()
#        map(self.call,dbconfigs)
#        print '=== handle done'

    help = "Start or stop mirroring data from Target Oracle Database. "

    def add_arguments(self, parser):
        """
        Args:
            parser (argparser.ArgumentParser):

        """
        actions = ['open', 'close', 'start', 'stop', 'status', 'restart', 'reborn']
        parser.add_argument(
            '-a', '--action',
            choices=actions,
            required=True,
            help='Actions is: <%s>' % '|'.join(actions)
        )

        targets = [x.name for x in OracleTarget.objects.all()]
        #targets.append(None)
        parser.add_argument(
            '-t', '--targets',
            nargs='*',
            choices=targets,
            default=targets,
            help='Targets can be empty or some of [%s]' % '|'.join(targets)
        )

    def handle(self, *args, **options):
        print args
        print options
        #action = options["action"]

