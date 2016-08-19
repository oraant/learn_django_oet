from os import system

from django.test import TestCase

from mirror.libs import cache
from mirror.libs import exceptions
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


class CacheTest(TestCase):
    """Unit test for Cache"""

    def setUp(self):
        # init data into tmp orm table

        gc_handler.reset()
        dc_handler.reset()
        pt_handler.reset()

        # get basic variables

        self.dbconfig = DBConfigs.objects.get(name="db11g")
        self.table = PTOra11gR2.objects.get(name="test_v$sysstat")
        self._format(self.table)
        self.datas = [(15, 'DB time', 3, 2777336, 3649082374)]

        # make sure mysql is started

        system("sudo service mysql start > /dev/null")

    def _format(self, table):
        """format table sqls,replace <TABLE_NAME>"""

        name = self.dbconfig.name + '_' + table.name
        table.create = table.create.replace("<TABLE_NAME>", name)
        table.drop = table.drop.replace("<TABLE_NAME>", name)
        table.insert = table.insert.replace("<TABLE_NAME>", name)
        table.delete = table.delete.replace("<TABLE_NAME>", name)

    # test __init__() abnormal

    def test_init_with_config_miss(self):
        GlobalConfigs.objects.get(name="mysql_port").delete()

        with self.assertRaises(exceptions.ConfigGetError):
            c = cache.Cacher()

    def test_init_with_mysql_connect_fail(self):
        row = GlobalConfigs.objects.get(name="mysql_password")
        row.value = "wrongpassword"  # mutable
        row.save()

        with self.assertRaises(exceptions.MySQLConnectError):
            c = cache.Cacher()

    def test_init_with_config_mistake(self):
        row = GlobalConfigs.objects.get(name="mysql_host")
        row.value = "192.168.111.111"  # mutable
        row.save()

        with self.assertRaises(exceptions.MySQLConnectError):
            c = cache.Cacher()

    # test cache() abnormal

    def test_cache_with_connection_closed(self):
        c = cache.Cacher()
        c.cache(self.table, self.datas)
        c.close()
        with self.assertRaises(exceptions.MySQLOperationError):
            c.cache(self.table, self.datas)

    def test_cache_with_create_sql_syntax_error(self):
        self.table.create = '''
            create IF NOT EXISTS <TABLE_NAME>(
                statistic bigint,
                name varchar(64),
                class bigint,
                value bigint,
                stat_id bigint)
            ENGINE = MEMORY
        '''  # mutable
        self._format(self.table)

        c = cache.Cacher()

        with self.assertRaises(exceptions.MySQLOperationError):
            c.cache(self.table, self.datas)
        c.close()

    def test_cache_with_delete_sql_syntax_error(self):
        self.table.delete = ''' delete * from <TABLE_NAME> '''  # mutable
        self._format(self.table)

        c = cache.Cacher()

        with self.assertRaises(exceptions.MySQLOperationError):
            c.cache(self.table, self.datas)
        c.close()

    def test_cache_with_delete_table_name_error(self):
        self.table.delete = ''' delete from wrongtabl '''  # mutable
        self._format(self.table)

        c = cache.Cacher()

        with self.assertRaises(exceptions.MySQLOperationError):
            c.cache(self.table, self.datas)

    def test_cache_with_insert_sql_syntax_error(self):
        self.table.insert = '''
            insert into <TABLE_NAME>
                (statistic,name,class,value,wrongcolumn)
                values (%s,%s,%s,%s,%s)
        '''  # mutable

        self._format(self.table)

        c = cache.Cacher()

        with self.assertRaises(exceptions.MySQLOperationError):
            c.cache(self.table, self.datas)
        c.close()

    def test_cache_with_insert_sql_colums_error(self):
        self.table.insert = '''
            insert into <TABLE_NAME>
                (statistic,name,class,value,stat_id)
                values (%s,%s,%s,%s)
        '''  # mutable

        self._format(self.table)

        c = cache.Cacher()

        with self.assertRaises(exceptions.MySQLOperationError):
            c.cache(self.table, self.datas)
        c.close()

    def test_cache_with_wrong_data_column(self):
        self.datas = [(15, 'DB time', 3, 2777336)]  # mutable

        c = cache.Cacher()

        with self.assertRaises(exceptions.MySQLOperationError):
            c.cache(self.table, self.datas)
        c.close()

    # test close() abnormal

    def test_close_with_drop_sql_syntax_error(self):
        self.table.drop = ''' drop <TABLE_NAME> '''
        self._format(self.table)

        c = cache.Cacher()
        c.cache(self.table, self.datas)

        with self.assertRaises(exceptions.MySQLOperationError):
            c.close()

    # test __init__() and cache() and close()

    def test_init_and_cache(self):
        c = cache.Cacher()
        c.cache(self.table, self.datas)
        result = c.show("select * from db11g_test_v$sysstat")  # mutable # todo : now
        self.assertEquals(result[0][0], 15)
        c.close()