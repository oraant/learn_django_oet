from mirror.libs.exceptions import NotEnableError, ORACLEConnectError, ORACLEOperationError
import cx_Oracle


class Puller(object):
    """
    Pull data from target oracle database.

    Attributes:
        dsn: (mirror.models.OracleTarget): get connection msg to connect with target oracle database.
        connection (cx_Oracle.Connection): connection to target oracle database.
    """

    def __str__(self):
        return "Puller for %s" % self.dsn.name

    def __init__(self, dsn):
        """
        Connect to target oracle database.

        Args:
            dsn (mirror.models.OracleTarget): get connection msg to connect with target oracle database.

        Raises:
            NotEnableError: The dsn is configured as not enable.
            ORACLEConnectError: Can't connect to target oracle database with this dsn.
        """

        # get dsn for connection
        if dsn.enable:
            self.dsn = dsn
        else:
            raise NotEnableError("Puller is not enabled.")

        # get connection
        try:
            self.connection = cx_Oracle.connect(dsn.user, dsn.password, dsn.dns(), threaded=True)
        except (cx_Oracle.InterfaceError, cx_Oracle.DatabaseError) as e:
            raise ORACLEConnectError("Error: %s. DSN: %s" % (e, dsn.dns()))

    def close(self):
        """
        Disconnect from target database. Calling close() more than once is allowed.

        Returns:
            str: result status of closing connection.
        """

        try:
            self.connection.close()
        except cx_Oracle.InterfaceError as e:
            msg = "Puller to %s has been closed with nothing opening.Msg is %s" % (self.dsn.name, e)
        else:
            msg = "Puller to %s has been closed." % self.dsn.name

        return msg

    def pull(self, table):
        """
        Pull data from target database with generating a cursor and executing the pull sql of table arg.

        Args:
            table (mirror.models.TableCollections): the target Oracle's table to pull data from.

        Raises:
            ORACLEConnectError: get cursor from connection failed.Maybe
            ORACLEOperationError: cursor can't execute sql statements.

        Returns:
            list[tuple]: All data pulled from target table.

        """

        # get cursor from connection
        try:
            cursor = self.connection.cursor()
        except cx_Oracle.InterfaceError as e:
            raise ORACLEConnectError(e)

        # execute sql statement to get data, and close cursor finally.
        # todo: sql maybe hanged because of network error or server overload.Stop it and raise error for interval run.
        try:
            cursor.execute(table.pull)
        except cx_Oracle.DatabaseError as e:
            raise ORACLEOperationError(e)
        else:
            return cursor.fetchall()
        finally:
            cursor.close()
