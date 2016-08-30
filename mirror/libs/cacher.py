from mirror.libs.exceptions import NotEnableError, MySQLConnectError, MySQLOperationError
import MySQLdb
import warnings


class Cacher:

    """
    Cache data to mysql database's temporary tables.

    Attributes:
        connection (MySQLdb.connections.Connection): connection to MySQL server.
    """

    def __init__(self, dsn, db_name):

        """
        Connect to MySQL server and generate a database to create temporary tables.

        Args:
            dsn (mirror.models.MySQLServer): MySQL Server connect information.
            db_name (str): database name in the MySQL server to create cache tables.

        Raises:
            NotEnableError: The dsn is configured as not enable.
            MySQLConnectError: Can't connect to MySQL Server with the dsn or can't create new databases.
        """

        # ignore special warnings for now and further calling of functions.
        # self._ignore_warnings()

        # make sure the dsn in enabled.
        if dsn.enable:
            self.dsn = dsn
        else:
            raise NotEnableError("Cacher is not enabled.")

        # get connection
        try:
            self.connection = MySQLdb.connect(host=dsn.host, user=dsn.user, passwd=dsn.password, port=dsn.port)
        except MySQLdb.OperationalError as e:
            raise MySQLConnectError(e)

        # format the database name, then create and connect to it.
        cursor = self.connection.cursor()
        self.db = dsn.prefix + db_name
        sql = "CREATE DATABASE IF NOT EXISTS %s DEFAULT CHARACTER SET utf8" % self.db

        try:
            cursor.execute(sql)
        except MySQLdb.OperationalError as e:
            cursor.close()
            self.connection.close()
            raise MySQLConnectError(e)
        else:
            cursor.close()
            self.connection.select_db(self.db)

    @staticmethod
    def _ignore_warnings():
        """ignore warnings when create or drop databases and tables. This method doesn't handle exceptions."""
        # todo: optimize to model method with a standard docstring and goodness performance.
        # todo-warning: database exists won't be filter but the cache method's can be filter
        ignore_warns = ["database exists", "database doesn't exist", "Table .* already exists", "Unknown table"]
        warnings.filterwarnings("ignore", '|'.join(ignore_warns))

    def cache(self, table, data):
        """
        Update data into cache tables.

        Args:
            table (mirror.models.TableCollections): a table with sql statements.
            data (list[tuple]): data you want to cache into table.

        Raises:
            MySQLConnectError: cursor can't connect to server,or permission denied, or others.
            MySQLOperationError: sql statements have syntax,or doesn't compatibly with data.
        """

        cursor = self.connection.cursor()  # this will not raise exceptions even the connection is closed.

        try:
            cursor.execute(table.create)
            cursor.execute(table.delete)
            cursor.executemany(table.insert, data)

        # maybe you want to generate a cursor after connection is closed.
        except MySQLdb.InterfaceError as e:
            raise MySQLConnectError(e)

        # MySQL server closed, or permission denied, or others.
        except MySQLdb.OperationalError as e:
            raise MySQLConnectError(e)

        # sql statements have syntax error.
        except MySQLdb.ProgrammingError as e:
            raise MySQLOperationError(e)

        # data columns's number is not equal to sql statements's values number.
        except TypeError as e:
            raise MySQLOperationError(e)

        finally:
            cursor.close()

    def close(self):
        """
        Close self.connection. Calling close() more than once is allowed.

        Returns:
            str: result status of closing connection.
        """

        try:
            self.connection.close()
        except MySQLdb.ProgrammingError as e:
            msg = "Cacher for %s has been closed with nothing opening.Msg is %s" % (self.dsn.name, e)
        else:
            msg = "Cacher for %s has been closed." % self.dsn.name

        return msg
