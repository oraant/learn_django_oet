import cx_Oracle
from mirror.libs.exceptions import NotEnableError, ORACLEConnectError, ORACLEOperationError


class Puller(object):

    """

    """

    def __init__(self, dsn):

        """
        Get connection with target database if it's enabled.
        :param dsn: instance of OracleTarget model
        """

        self.dsn = dsn
        self._connect()

    def _connect(self):

        """connect to target database

        Exceptions:
            exceptions.ConfigGetError
            exceptions.ORACLEConnectError
        """

        try:
            user = self.dbconfig.user
            password = self.dbconfig.password
            dns = self.dbconfig.ip + ":" + self.dbconfig.port + "/" + self.dbconfig.service
        except Exception as e:
            msg = "Configs Get Error,please your configs. %s" % e
            raise exceptions.ConfigGetError(msg)

        try:
            self.connection = cx_Oracle.connect(user,password,dns,threaded = True) # raise
            print dns
        except Exception as e:
            msg = "Connect to target oracle db failed,dns is %s. %s" % (dns,e)
            raise exceptions.ORACLEConnectError(msg)

    def _disconnect(self):
        """disconnect from target database"""
        self.connection.close()

    def pull(self,table):
        """pull datas"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(table.pull)
            datas = cursor.fetchall()
        finally:
            cursor.close()
        return datas

    def close(self):
        """close connection"""
        self._disconnect()
