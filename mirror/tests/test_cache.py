from django.test import TestCase
from mirror.libs import cacher
import mirror.models as models
import MySQLdb

# todo : some open should be closed after raise exceptions like asserts


class CacheTest(TestCase):

    fixtures = ['test.json']

    def setUp(self):

        self.target = models.OracleTarget.objects.get(name="db11g")
        self.table_collections = getattr(models, self.target.table_collection)
        self.tables = self.table_collections.objects.all()
        self.data = [
            (363264677, 'DB11G', 'READ WRITE', 'NOARCHIVELOG'),
            (363264677, 'DB11G', 'READ WRITE', 'NOARCHIVELOG')
        ]

        dsn = self.target.mysql
        self.dsn = dsn
        self.connection = MySQLdb.connect(host=dsn.ip, user=dsn.user, passwd=dsn.password, port=dsn.port)

    def test_function(self):

        c = cacher.Cacher(self.target.mysql, self.target.name)

        try:
            c.cache(self.tables[0], self.data)
        finally:
            c.close()

        self.connection.select_db(self.dsn.prefix + self.target.name)
        cursor = self.connection.cursor()
        cursor.execute("select * from %s" % self.tables[0].name)
        print cursor.fetchall()
        cursor.close()

    def tearDown(self):
        self.connection.close()
