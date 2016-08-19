from django.test import TestCase

from mirror.libs import pull
from mirror.models import GlobalConfigs, DBConfigs, PTOra11gR2
from orm.datas import globalconfigs, dbconfigs, ptora11gr2

# prepare init data for tables in test database

gc_handler = globalconfigs.Handler()
dc_handler = dbconfigs.Handler()
pt_handler = ptora11gr2.Handler()

gc_handler.orm = GlobalConfigs
dc_handler.orm = DBConfigs
pt_handler.orm = PTOra11gR2

# todo : some open should be closed after raise exceptions like asserts


class PullTest(TestCase):

    def setUp(self):

        # put init datas into tmp orm table

        gc_handler.putin()
        dc_handler.putin()
        pt_handler.putin()

        # get basic varibles

        self.dbconfig = DBConfigs.objects.get(name="db11g")
        self.table = PTOra11gR2.objects.get(name="test_v$sysstat")


    # test __init__() abnormal

    def test_init_with_config_error(self):

        self.dbconfig.host=3
        self.puller = pull.Puller(self.dbconfig)

        #with self.assertRaises(exceptions.ConfigGetError):
        #    self.puller = pull.Puller(self.dbconfig)
