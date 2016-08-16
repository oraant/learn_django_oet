from django.test import TestCase

from os import system
import time

from puller.libs import pull
from puller.libs import exceptions

# gc orm table
from puller.models import GlobalConfigs
from puller.datas import globalconfigs_handler
gchandler = globalconfigs_handler.Handler()
gchandler.orm = GlobalConfigs

# dc orm table
from puller.models import DBConfigs
from puller.datas import dbconfigs_handler
dchandler = dbconfigs_handler.Handler()
dchandler.orm = DBConfigs

# pt orm table
from puller.models import PTOra11gR2
from puller.datas import ptora11gr2_handler
pthandler = ptora11gr2_handler.Handler()
pthandler.orm = PTOra11gR2

# todo : some open should be closed after raise exceptions like asserts

class PullTest(TestCase):

    def setUp(self):

        # put init datas into tmp orm table

        gchandler.putin()
        dchandler.putin()
        pthandler.putin()

        # get basic varibles

        self.dbconfig = DBConfigs.objects.get(name="db11g")
        self.table = PTOra11gR2.objects.get(name="test_v$sysstat")


    # test __init__() abnormal

    def test_init_with_config_error(self):

        self.dbconfig.host=3
        self.puller = pull.Puller(self.dbconfig)

        #with self.assertRaises(exceptions.ConfigGetError):
        #    self.puller = pull.Puller(self.dbconfig)
