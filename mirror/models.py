# coding:utf-8
from django.db import models
from django.core.validators import RegexValidator
from datetime import timedelta
from django.conf import settings
from os.path import join

# configs for this model.


class GlobalConfig(models.Model):
    """Global configs with mirror model"""

    LOG_LEVEL = (
        (0, 'NOTSET'),
        (10, 'DEBUG'),
        (20, 'INFO'),
        (30, 'WARNING'),
        (40, 'ERROR'),
        (50, 'CRITICAL'),
    )

    class Meta:
        verbose_name = "Global Config"
        verbose_name_plural = "Global Configs"

    name = models.CharField(max_length=30, unique=True)
    enable = models.BooleanField(default=True, help_text="NOTICE!! Only one row can be enabled!!")
    desc = models.CharField(max_length=300)

    run = models.BooleanField(default=True, help_text="Do you want to start or stop this model at web level.(Unusable)")

    log_file = models.CharField(max_length=100, default=join(settings.BASE_DIR, 'data', 'mirror.log'))
    log_level = models.IntegerField(default=30, choices=LOG_LEVEL)
    log_size = models.IntegerField(default=10, help_text="Logfile's size, Unit is MB. Max is 32767 MB.")
    log_count = models.IntegerField(default=3, help_text="Backup logs count.")
    log_format = models.CharField(max_length=100, default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    sock_addr = models.GenericIPAddressField(
        default="127.0.0.1",
        help_text="listening Address."
    )
    sock_port = models.IntegerField(default=15521, help_text="Which port to bind the socket server in Mirror.")

    processes = models.IntegerField(default=4, help_text="Max number of processes.(Unusable)")
    reborn = models.DurationField(
        default=timedelta(0, 7200),
        help_text="When can't connect with server, how many seconds to wait to retry. Eg: 0:01:10 for 70 seconds."
    )

    def __unicode__(self):
        return self.name


# table collections with sql statements for pull and cache,abstract class and subclasses all here.


class TableCollections(models.Model):
    """SQLs the process need if you want to mirror Target tables."""

    class Meta:
        abstract = True

    # validators

    oracle_special_sign = RegexValidator(regex=r';', inverse_match=True, message="Please Don't Input signs like ';'")
    mysql_special_sign = RegexValidator(regex=r';|#', inverse_match=True,
                                        message="Please Don't Input signs like ';' , '#'")
    if_not_exists = RegexValidator(regex=r'(?i)if not exists', message="sql missed 'IF NOT EXISTS' !")
    if_exists = RegexValidator(regex=r'(?i)if exists', message="sql missed 'IF EXISTS' !")
    engine_is_memory = RegexValidator(regex=r'(?i)engine.*=.*memory', message="sql missed 'ENGINE = MEMORY' !")
    placeholder = RegexValidator(regex=r'\%s', message="sql missed %s !")

    # Validators collections

    oracle_sql_validators = [oracle_special_sign]
    create_sql_validators = [mysql_special_sign, if_not_exists, engine_is_memory]
    insert_sql_validators = [mysql_special_sign, placeholder]
    drop_validators = [mysql_special_sign, if_exists]
    delete_validators = [mysql_special_sign]

    # fields

    name = models.CharField(max_length=30, unique=True)
    enable = models.BooleanField(default=True)
    desc = models.CharField(max_length=300)
    period = models.DurationField(help_text="Format is like 0:01:10 for 70 seconds.")

    pull = models.TextField(max_length=900, validators=oracle_sql_validators)
    create = models.TextField(max_length=900, validators=create_sql_validators)
    drop = models.TextField(max_length=900, validators=drop_validators)  # won't be used in this version.
    insert = models.TextField(max_length=900, validators=insert_sql_validators)
    delete = models.TextField(max_length=900, validators=delete_validators)

    @classmethod
    def subclass_name(cls):
        return cls._meta.verbose_name_plural

    def __unicode__(self):
        return self.name


class OraTest(TableCollections):
    """Tables of Oracle whose version is 11gR2."""

    class Meta:
        verbose_name = "[Table Collections] Oracle Test's table"
        verbose_name_plural = "[Table Collections] Oracle Test"


class Ora10g(TableCollections):
    """Tables of Oracle whose version is 11gR2."""

    class Meta:
        verbose_name = "[Table Collections] Oracle 10G's table"
        verbose_name_plural = "[Table Collections] Oracle 10G"


class Ora11g(TableCollections):
    """Tables of Oracle whose version is 11gR2."""

    class Meta:
        verbose_name = "[Table Collections] Oracle 11G's table"
        verbose_name_plural = "[Table Collections] Oracle 11G"


class Ora12c(TableCollections):
    """Tables of Oracle whose version is 11gR2."""

    class Meta:
        verbose_name = "[Table Collections] Oracle 12C's table"
        verbose_name_plural = "[Table Collections] Oracle 12C"

# servers for redis and mysql, and target oracle databases.


class RedisServer(models.Model):
    """Redis Server you want to record status"""

    class Meta:
        verbose_name = "Redis Server"
        verbose_name_plural = "Redis Servers"

    name = models.CharField(max_length=30, unique=True)
    enable = models.BooleanField(default=True)
    desc = models.CharField(max_length=300)

    host = models.GenericIPAddressField()
    port = models.IntegerField()
    password = models.CharField(max_length=30, blank=True, null=True)

    def __unicode__(self):
        return self.name


class MySQLServer(models.Model):
    """MySQL Server you want to cache datas"""

    class Meta:
        verbose_name = "MySQL Server"
        verbose_name_plural = "MySQL Servers"

    name = models.CharField(max_length=30, unique=True)
    enable = models.BooleanField(default=True)
    desc = models.CharField(max_length=300)

    host = models.GenericIPAddressField(help_text='Use 127.0.0.1 instead of localhost to enforce port')
    port = models.IntegerField(help_text='Will not work if ip is localhost')
    user = models.CharField(max_length=30, help_text="the user need privileges to create or drop databases and tables!")
    password = models.CharField(max_length=30, blank=True, null=True)
    prefix = models.CharField(max_length=30, default="mirror_",
                              help_text="prefix of databases' name to avoid name conflict.")

    def __unicode__(self):
        return self.name


class OracleTarget(models.Model):
    """Targets oracle database you want to monitor."""

    class Meta:
        verbose_name = "Oracle Target"
        verbose_name_plural = "Oracle Targets"

    # validators

    special_sign = RegexValidator(
        regex=r'^[a-zA-Z0-9_]+$',
        message="Only allow a-z A-Z 0-9 and '_'"
    )

    # choices
    table_sql_list = [(x.__name__, x.subclass_name()) for x in TableCollections.__subclasses__()]
    CollectionChoices = tuple(table_sql_list)

    # fields
    name = models.CharField(max_length=30, unique=True)
    enable = models.BooleanField(default=True)
    desc = models.CharField(max_length=300)

    version = models.CharField(max_length=30)
    rac = models.BooleanField(default=False)
    dbid = models.CharField(max_length=30)
    instance = models.IntegerField()

    host = models.GenericIPAddressField()
    port = models.IntegerField()
    user = models.CharField(max_length=30)
    password = models.CharField(max_length=30, blank=True, null=True)
    service = models.CharField(max_length=30)

    table_collection = models.CharField(max_length=30, choices=CollectionChoices)
    mysql_server = models.ForeignKey(MySQLServer)
    mysql_db = models.CharField(max_length=50, unique=True, validators=[special_sign], help_text='mysql database name.')
    redis_server = models.ForeignKey(RedisServer)
    redis_db = models.IntegerField(unique=True, help_text='redis db number, must be unique.')
    # todo : mysql_db and redis_db should not be unique, but use a validator to make sure it's unique.

    def __unicode__(self):
        return self.name

    def dns(self):
        return "%s:%d/%s" % (self.host, self.port, self.service)
