"""Exceptions for Oracle Expert Tools

This classes are imitate from _msyql_exceptions of MySQLdb.
"""

class BaseException(Exception):

    """Exception related to operation with OET."""

    def __init__(self,value):
        self.value=value

    def __str__(self):
        return repr(self.value)


class MySQLConnectError(BaseException):

    """Exception raised when connect failed with MySQL"""

class MySQLOperationError(BaseException):

    """Exception raised for when create/drop tables or insert/delete datas in MySQL"""

class ORACLEConnectError(BaseException):

    """Exception raised for when connect with Oracle"""

class ORACLEOperationError(BaseException):

    """Exception raised for when create/drop tables or insert/delete datas in MySQL"""

class RedisConnectError(BaseException):

    """Exception raised for when connect with Redis"""

class ConfigGetError(BaseException):

    """Exception raised for when get Configs from Django ORM Tables"""
