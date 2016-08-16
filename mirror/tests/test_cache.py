from django.test import TestCase

from os import system
import time
import MySQLdb

from puller.libs import cache
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

class CacheTest(TestCase):

    def setUp(self):

        # put init datas into tmp orm table

        gchandler.putin()
        dchandler.putin()
        pthandler.putin()

        # get basic varibles

        self.dbconfig = DBConfigs.objects.get(name="db11g")
        self.table = PTOra11gR2.objects.get(name="test_v$sysstat")
        self._format(self.table)
        self.datas=[(15,'DB time',3,2777336,3649082374)]

        # make sure mysql is started

        system("service mysqld start > /dev/null")


    def _format(self,table):

        '''format table sqls,replace <TABLE_NAME>'''

        name = self.dbconfig.name + '_' + table.name
        table.create = table.create.replace("<TABLE_NAME>",name)
        table.drop = table.drop.replace("<TABLE_NAME>",name)
        table.insert = table.insert.replace("<TABLE_NAME>",name)
        table.delete = table.delete.replace("<TABLE_NAME>",name)


    # test __init__() abnormal

    def test_init_with_config_miss(self):

        GlobalConfigs.objects.get(name="mysql_port").delete()

        with self.assertRaises(exceptions.ConfigGetError):
            c=cache.Cacher(self.dbconfig)

    def test_init_with_mysql_connect_fail(self):

        row=GlobalConfigs.objects.get(name="mysql_password")
        row.value="wrongpassword" # mutable
        row.save()

        with self.assertRaises(exceptions.MySQLConnectError):
            c=cache.Cacher(self.dbconfig)

    def test_init_with_config_mistake(self):

        row=GlobalConfigs.objects.get(name="mysql_host")
        row.value="192.168.1111.1111" # mutable
        row.save()

        with self.assertRaises(exceptions.MySQLConnectError):
            c=cache.Cacher(self.dbconfig)


    # test cache() abnormal

    def test_cache_with_connection_closed(self):

        c=cache.Cacher(self.dbconfig)
        c.cache(self.table,self.datas)
        c.close()
        with self.assertRaises(exceptions.MySQLOperationError):
            c.cache(self.table,self.datas)

    def test_cache_with_create_sql_syntax_error(self):

        self.table.create = '''
            create IF NOT EXISTS <TABLE_NAME>(
                statistic bigint,
                name varchar(64),
                class bigint,
                value bigint,
                stat_id bigint)
            ENGINE = MEMORY
        ''' # mutable
        self._format(self.table)

        c=cache.Cacher(self.dbconfig)

        with self.assertRaises(exceptions.MySQLOperationError):
            c.cache(self.table,self.datas)
        c.close()

    def test_cache_with_delete_sql_syntax_error(self):

        self.table.delete = ''' delete * from <TABLE_NAME> ''' # mutable
        self._format(self.table)

        c=cache.Cacher(self.dbconfig)

        with self.assertRaises(exceptions.MySQLOperationError):
            c.cache(self.table,self.datas)
        c.close()

    def test_cache_with_delete_table_name_error(self):

        self.table.delete = ''' delete from wrongtabl ''' # mutable
        self._format(self.table)

        c=cache.Cacher(self.dbconfig)

        with self.assertRaises(exceptions.MySQLOperationError):
            c.cache(self.table,self.datas)

    def test_cache_with_insert_sql_syntax_error(self):

        self.table.insert = '''
            insert into <TABLE_NAME>
                (statistic,name,class,value,wrongcolumn)
                values (%s,%s,%s,%s,%s)
        ''' # mutable

        self._format(self.table)

        c=cache.Cacher(self.dbconfig)

        with self.assertRaises(exceptions.MySQLOperationError):
            c.cache(self.table,self.datas)
        c.close()

    def test_cache_with_insert_sql_colums_error(self):

        self.table.insert = '''
            insert into <TABLE_NAME>
                (statistic,name,class,value,stat_id)
                values (%s,%s,%s,%s)
        ''' # mutable

        self._format(self.table)

        c=cache.Cacher(self.dbconfig)

        with self.assertRaises(exceptions.MySQLOperationError):
            c.cache(self.table,self.datas)
        c.close()

    def test_cache_with_wrong_data_column(self):

        self.datas=[(15,'DB time',3,2777336)] # mutable

        c=cache.Cacher(self.dbconfig)

        with self.assertRaises(exceptions.MySQLOperationError):
            c.cache(self.table,self.datas)
        c.close()

    # test close() abnormal

    def test_close_with_drop_sql_syntax_error(self):

        self.table.drop = ''' drop <TABLE_NAME> '''
        self._format(self.table)

        c=cache.Cacher(self.dbconfig)
        c.cache(self.table,self.datas)

        with self.assertRaises(exceptions.MySQLOperationError):
            c.close()

    # test __init__() and cache()

    def test_init_and_cache(self):

        c=cache.Cacher(self.dbconfig)
        c.cache(self.table,self.datas)
        result=c.show("select * from db11g_test_v$sysstat") # mutable # todo : now
        self.assertEquals(result[0][0],15)
        c.close()
