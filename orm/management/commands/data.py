# coding:utf-8

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from puller.datas import globalconfigs_handler # mutable
from puller.datas import dbconfigs_handler # mutable
from puller.datas import ptora11gr2_handler # mutable

class Command(BaseCommand):
    args = '<Action> <Orm>'

    actions = ['putin','show','clear','reset'] # mutable
    helparg = '<%s> <orm ...|all>' % '|'.join(actions) # mutable
    models = [ globalconfigs_handler, dbconfigs_handler, ptora11gr2_handler ] # mutable # todo: optimize

    help  = '  This command helps you manage datas for ORM tables of app configs.\n' # mutable
    help += '\n'
    help += 'Syntax should be this:\n'
    help += '\n'
    help += '  ./manage.py data [options] %s\n' % helparg
    help += '\n'
    help += 'Action:\n'
    help += '  putin \t-\t Put original datas in your ORM tables\n'
    help += '  show  \t-\t Show name of every row in your ORM tables\n'
    help += '  clear \t-\t Delete every row of your ORM tables\n'
    help += '  reset \t-\t Delete current datas and put original datas in your ORM table\n'
    help += '\n'
    help += 'Orm:\n'
    help += '  orm \t\t-\t the class name of ORM which you write in App.Models,\n'
    help += '      \t\t\t like GlobalConfigs\n'
    help += '  all \t\t-\t all ORM which you write in App.Models'

    def handle(self, *args, **options):
        ''' make sure args are ok '''
        # make sure args is enough
        try:
            self.action = args[0]
            self.orms = args[1:]
        except Exception,e:
            self.stdout.write('\n\tSyntax Error: Not Enough args.  Use -h for help\n\n')
            exit(1)

        # make sure action is legal
        if not self.action in self.actions:
            self.stdout.write('\n\tSyntax Error: Unkown action.  Use -h for help\n\n')
            exit(2)

        self.get_models()
        self.act_handlers()

    def get_models(self):
        ''' get data handler modes for orm tables '''

        # orms is all
        if  self.orms[0] == 'all':
            return

        # orms is not all
        try:
            self.models = [ eval(x.lower()+"_handler") for x in self.orms ]
        except NameError,e:
            self.stdout.write('\n\tSyntax Error: Unkown ORM.  Use -h for help\n\n')
            exit(3)
        except Exception,e:
            self.stdout.write('\n\tSyntax Error: %s.  Use -h for help\n\n' % e)
            exit(4)

    def act_handlers(self):
        ''' map the handler models to method '''
        print
        map(self.act_handler,self.models)

    def act_handler(self,model):
        ''' do the actions use the handler '''
        self.stdout.write('[%s] Action Starting...' % model.__name__)

        try:
            handler=model.Handler()
            exec("handler.%s()" % self.action)
        except Exception,e:
            self.stdout.write('[%s] %sAction Failed%s.'%(model.__name__,'\033[4;31m','\033[0m'))
            self.stdout.write(str(e))

        self.stdout.write('[%s] Action Done!\n' % model.__name__)
        self.stdout.write('')
