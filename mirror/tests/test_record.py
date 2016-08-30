from django.test import TestCase
from mirror.libs import recorder
import mirror.models as models
import time
import redis


class RecordTest(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.target = models.OracleTarget.objects.get(name="db11g")
        self.dsn = self.target.redis_server
        self.db_number = self.target.redis_db
        self.connection = redis.Redis(host=self.dsn.host,
                                      port=self.dsn.port,
                                      password=self.dsn.password,
                                      db=self.db_number)

    def test_function(self):
        r = recorder.Recorder(self.dsn, self.db_number)
        r.record("test key", 2)

        time.sleep(1)
        self.assertTrue(self.connection.get("test key"))

        time.sleep(2)
        self.assertFalse(self.connection.get("test key"))

