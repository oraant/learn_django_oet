from mirror.libs.exceptions import NotEnableError, RedisConnectError, RedisOperationError
import redis


class Recorder:
    """
    Attributes:
        connection (redis.client.Redis): connection to redis server.
    """

    def __str__(self):
        return "Recorder for %s" % self.dsn.name

    def __init__(self, dsn, db_number):
        """
        Connect to Redis Server.

        Args:
            dsn (mirror.models.RedisServer): Redis Server connect information.
            db_number (long): The id of target oracle database.

        Raises:
            NotEnableError:  The dsn is configured as not enable.
            RedisConnectError: Can't connect to Redis Server.
            Exception: Interval Unknown error.
        """

        # make sure dsn is enabled
        if dsn.enable:
            self.dsn = dsn
        else:
            raise NotEnableError("Redis is not enabled.")

        # get redis server
        self.db_number = db_number

        # get connection
        try:
            self.connection = redis.Redis(host=dsn.host, port=dsn.port, password=dsn.password, db=db_number)
        except (redis.ResponseError, redis.AuthenticationError) as e:
            raise RedisConnectError(e)

    def record(self, name, seconds):
        """
        Record with True value for every table with a expired time.

        Notes:
            The expired time is 1.5 times of the period seconds.

        Args:
            name (str): the table name you want to record
            seconds (int): the period seconds when pull tables.

        Raises:
            RedisConnectError: can't connect to server or record failed.
            RedisOperationError: set value failed.
            Exception: Interval Unknown error.
        """

        expired = int(seconds * 1.5)

        try:
            result = self.connection.set(name, True, expired)
        except (redis.ResponseError, redis.Connection) as e:
            raise RedisConnectError(e)

        if not result:
            raise RedisOperationError("Set value into Redis failed. DB=%s, Key=%s." % (self.db_number, name))

    def close(self):
        return "Recorder to %s has been closed." % self.dsn.name
