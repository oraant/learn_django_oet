from mirror.libs.exceptions import NotEnableError, ORACLEConnectError, ORACLEOperationError
import cx_Oracle


class Puller(object):
    """
    Pull data from target oracle database.

    Attributes:
        connection (cx_Oracle.Connection): connection to target oracle database.
    """

    def __init__(self, dsn):
        """
        Connect to target oracle database.

        Args:
            dsn: (mirror.models.OracleTarget): get connection msg to connect with target oracle database.

        Raises:
            NotEnableError: If the dsn is configured as not enable, this will be raised.
            ORACLEConnectError: If can't connect to target with this dsn, this will be raised.
        """

        # get dsn for connection
        if dsn.enable:
            self.dsn = dsn
        else:
            raise NotEnableError("Puller is not enabled.")

        # get connection
        try:
            self.connection = cx_Oracle.connect(dsn.user, dsn.password, dsn.dns(), threaded=True)
        except cx_Oracle.InterfaceError as e:
            raise ORACLEConnectError(e)

    def close(self):
        """
        Disconnect from target database. Calling close() more than once is allowed.

        Returns:
            str: result status of closing connection.
        """

        try:
            self.connection.close()
        except cx_Oracle.InterfaceError as e:
            msg = "Puller for %s has been closed with nothing opening." % self.dsn.name
        else:
            msg = "Puller for %s has been closed." % self.dsn.name

        return msg

    def pull(self, table):
        """
        Pull data from target database with generating a cursor and executing the pull sql of table arg.

        Args:
            table (mirror.models.TableSQL): the target Oracle's table to pull data from.

        Raises:
            ORACLEConnectError: get cursor from connection failed.Maybe
            ORACLEOperationError: cursor can't execute sql statements.

        Returns:
            list: All data pulled from target table, with the format [(value1, value2), (value1, value2)]

        """

        # get cursor from connection
        try:
            cursor = self.connection.cursor()
        except cx_Oracle.InterfaceError as e:
            raise ORACLEConnectError(e)

        # execute sql statement and get data
        # todo: sql maybe hanged because of network error or server overload.Stop it and raise error for interval run.
        try:
            cursor.execute(table.pull)
        except cx_Oracle.DatabaseError as e:
            raise ORACLEOperationError(e)
        else:
            return cursor.fetchall()
        finally:
            cursor.close()
