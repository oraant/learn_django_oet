# coding:utf-8

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):

    """Data command to handle datas with ORM tables."""

    help = "Handle ORM table's data"
    tables = ['globalconfigs', 'dbconfigs', 'ptora11gr2']   # mutable

    def add_arguments(self, parser):

        # name of action
        parser.add_argument(
            'action',
            metavar='action',
            choices=['putin', 'clear', 'show', 'reset'],
            help='Actions is: <putin|clear|show|reset>'
        )

        # name of ORM tables in models
        parser.add_argument(
            'tables',
            metavar='tables',
            nargs='*',
            choices=self.tables+['all'],
            default='all',
            help='ORM tables you want to handle,blank means ALL.'
        )

    def handle(self, *args, **options):

        # get tables if user typed all tables
        tables = options['tables']
        if 'all' in tables:
            tables = self.tables

        # get data handlers
        handlers = []
        for table in tables:
            exec "from orm.datas import %s" % table
            handlers.append(eval(table))

        # act data handlers
        action = options['action']
        for handler in handlers:
            name = handler.__name__
            self._output('[%s] Action Starting...' % name)

            try:
                handler = handler.Handler()
                exec "handler.%s()" % action
            except Exception as e:
                raise CommandError(e)

            self._output('[%s] Action Succeed!' % name)
            self._output('')

    def _output(self,msg):
        self.stdout.write(msg)