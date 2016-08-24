from django.test import TestCase
from mirror.libs import puller
import mirror.models as models
from importlib import import_module


class PullTest(TestCase):

    fixtures = ["m2.json"]

    def setUp(self):

        self.target = models.OracleTarget.objects.get(name="db11g")
        self.tables = getattr(models, self.target.tables)

    # test __init__() abnormal
    def test_init(self):
        p = puller.Puller(self.target)
        p.pull(self.tables.objects.all()[0])
        p.close()
