from puller.models import GlobalConfigs
import MySQLdb
from functools import partial

# cache exceptions

import _mysql_exceptions as msqexp
import exceptions

# main class

class Cacher:

    """cache datas to mysql database

    Exceptions:
        MySQLConnectError
        MySQLOperationError
        ORACLEConnectError 
    """

    # initial

    def __init__(self):

        """Init cacher instance"""

        self.tables=[] # the table names this cache created
        self._connect()

    # connections

    def _connect(self):

        """Connect to mysql server

        Exceptions:
            exceptions.ConfigGetError
            exceptions.MySQLConnectError
        """

        try:
            host = GlobalConfigs.objects.get(name="mysql_host").value
            user = GlobalConfigs.objects.get(name="mysql_user").value
            passwd = GlobalConfigs.objects.get(name="mysql_password").value
            port = GlobalConfigs.objects.get(name="mysql_port").value
            port = int(port)
            db = GlobalConfigs.objects.get(name="mysql_db").value
        except Exception,e:
            raise exceptions.ConfigGetError("Error : %s" % e)

        try:
            self.conn = MySQLdb.connect(host=host,
                                        user=user,
                                        passwd=passwd,
                                        db=db,
                                        port=port)
        except msqexp.OperationalError,e:
            raise exceptions.MySQLConnectError("Error : %s" % e)

    def _disconnect(self):

        """disconnect from mysql server"""

        self.conn.close()

    # operations

    def _create(self,cursor,table): # raise
        """create cache table if not exists,and ignore the exists warning"""
        try:
            cursor.execute(table.create)
        except msqexp.Warning,e:
            if str(e).find('already exists') == -1:
                raise
        except msqexp.ProgrammingError,e:
            msg = "Create cache table failed,Please Check your create sql. %s" % e
            raise exceptions.MySQLOperationError(msg)
        except msqexp.InterfaceError,e:
            msg = "Create cache table failed,Please Check your call order. %s" % e
            raise exceptions.MySQLOperationError(msg)


    def _drop(self,cursor,table): # raise
        """drop cache table"""
        try:
            cursor.execute(table.drop)
        except msqexp.ProgrammingError,e:
            msg = "Drop cache table failed,Please Check your drop sql. %s" % e
            raise exceptions.MySQLOperationError(msg)

    def _insert(self,cursor,table,datas): # raise
        """insert datas into cache table"""
        try:
            cursor.executemany(table.insert,datas)
        except (TypeError,
                msqexp.ProgrammingError,
                msqexp.OperationalError) as e:
            msg = "Insert datas failed,Please Check your insert sql or datas. %s" % e
            raise exceptions.MySQLOperationError(msg)

    def _delete(self,cursor,table): # raise
        """delete datas from cache table"""
        try:
            cursor.execute(table.delete)
        except msqexp.ProgrammingError,e:
            msg = "Delete datas failed,Please Check your delete sql. %s" % e
            raise exceptions.MySQLOperationError(msg)

    # interfaces

    def cache(self,table,datas):

        """update datas into cache tables

        Args:
            table -- orm row in pull tables,your must replace <TABLE_NAME> first
            datas -- datas pulled from target oracle,make sure it'a list with tuples

        Exceptions:
            exceptions.MySQLOperationError
        """

        cursor = self.conn.cursor()

        try:
            self._create(cursor,table)
            self._delete(cursor,table)
            self._insert(cursor,table,datas)
            self.tables.append(table)
        except exceptions.MySQLOperationError,e:
            raise
        finally:
            cursor.close()

    def show(self,sql):

        """use for unni test"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql)
            #def f(x):print x
            #map(f,cursor.fetchall())
            return cursor.fetchall()
        except Exception,e:
            raise
        finally:
            cursor.close()


    def close(self):

        """drop cache tables

        Exceptions:
            exceptions.MySQLOperationError
        """

        cursor = self.conn.cursor()
        drop = partial(self._drop,cursor)

        try:
            map(drop,self.tables)
        except exceptions.MySQLOperationError,e:
            raise
        finally:
            cursor.close()
            self._disconnect()
