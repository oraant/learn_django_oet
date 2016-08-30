from django.test import TestCase
from mirror.libs import puller
import mirror.models as models


class PullTest(TestCase):

    fixtures = ["test.json"]

    def setUp(self):

        self.target = models.OracleTarget.objects.get(name="db11g")
        self.table_collections = getattr(models, self.target.table_collection)
        self.tables = self.table_collections.objects.all()

    def test_function(self):

        p = puller.Puller(self.target)

        try:
            data = p.pull(self.tables[0])
            print data
            self.assertEqual(data[0][2], 'READ WRITE')
        finally:
            p.close()
