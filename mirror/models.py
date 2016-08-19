# coding:utf-8
from django.db import models
from django.core.validators import RegexValidator


# Create your models here.


class GlobalConfig(models.Model):

    """Global configs with mirror model"""

    LOG_LEVEL = (
        ('0', 'NOTSET'),
        ('10', 'DEBUG'),
        ('20', 'INFO'),
        ('30', 'WARNING'),
        ('40', 'ERROR'),
        ('50', 'CRITICAL'),
    )

    class Meta:
        verbose_name = "Global Config"
        verbose_name_plural = "Global Configs"

    name = models.CharField(max_length=30, unique=True)
    enable = models.BooleanField(default=True, help_text="NOTICE!! Only one row can be enabled!!")
    desc = models.CharField(max_length=300)

    run = models.BooleanField(default=True, help_text="Do you want to start or stop this model at web level.")
    log_level = models.CharField(max_length=50, choices=LOG_LEVEL)


class RedisServer(models.Model):

    """Redis Server you want to record status"""

    class Meta:
        verbose_name = "Redis Server"
        verbose_name_plural = "Redis Servers"

    name = models.CharField(max_length=30, unique=True)
    enable = models.BooleanField(default=True)
    desc = models.CharField(max_length=300)

    ip = models.GenericIPAddressField()
    port = models.CharField(max_length=30)
    password = models.CharField(max_length=30, blank=True, null=True)
    db = models.SmallIntegerField()

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

    ip = models.GenericIPAddressField(help_text='Use 127.0.0.1 instead of localhost to enforce port')
    port = models.CharField(max_length=30, help_text='Will not work if ip is localhost')
    user = models.CharField(max_length=30)
    password = models.CharField(max_length=30, blank=True, null=True)
    db = models.CharField(max_length=30)


class OracleTarget(models.Model):

    """Targets oracle database you want to monitor."""

    class Meta:
        verbose_name = "Oracle Target"
        verbose_name_plural = "Oracle Targets"

    TableSQLChoices = (
        ('Ora11gR2', 'Oracle 11G R2'),
    )

    name = models.CharField(max_length=30, unique=True)
    enable = models.BooleanField(default=True)
    desc = models.CharField(max_length=300)

    version = models.CharField(max_length=30)
    rac = models.BooleanField(default=False)
    dbid = models.CharField(max_length=30)
    instance = models.IntegerField()

    ip = models.GenericIPAddressField()
    port = models.CharField(max_length=30)
    user = models.CharField(max_length=30)
    password = models.CharField(max_length=30, blank=True, null=True)
    service = models.CharField(max_length=30)

    tables = models.CharField(max_length=30, choices=TableSQLChoices)


class TableSQL(models.Model):

    """SQLs the process need if you want to mirror Target tables."""

    class Meta:
        abstract = True

    # validators

    oracle_special_sign = RegexValidator(regex=r';', inverse_match=True, message="Please Don't Input signs like ';'")
    mysql_special_sign = RegexValidator(regex=r';|#', inverse_match=True,
                                        message="Please Don't Input signs like ';' , '#'")
    table_name = RegexValidator(regex=r'\<TABLE_NAME\>', message="Please Input <TABLE_NAME> !")
    if_not_exists = RegexValidator(regex=r'(?i)if not exists', message="Please Input 'IF NOT EXISTS' !")
    engine_is_memory = RegexValidator(regex=r'(?i)engine.*=.*memory', message="Please Input 'ENGINE = MEMORY' !")
    placeholder = RegexValidator(regex=r'\%s', message="Please Input %s !")

    # Validators collections

    oracle_sql_validators = [oracle_special_sign]
    create_sql_validators = [mysql_special_sign, table_name, if_not_exists, engine_is_memory]
    insert_sql_validators = [mysql_special_sign, table_name, placeholder]
    drop_delete_validators = [mysql_special_sign, table_name]

    # fields

    name = models.CharField(max_length=30, unique=True)
    enable = models.BooleanField(default=True)
    desc = models.CharField(max_length=300)
    period = models.DurationField(help_text="Format is like 0:01:10 for 70 seconds.")

    pull = models.TextField(max_length=900, validators=oracle_sql_validators)
    create = models.TextField(max_length=900, validators=create_sql_validators)
    drop = models.TextField(max_length=900, validators=drop_delete_validators)
    insert = models.TextField(max_length=900, validators=insert_sql_validators)
    delete = models.TextField(max_length=900, validators=drop_delete_validators)

    # functions

    def apply(self, name):

        """Replace name to <TABLE_NAME> in cache sql statements."""

        self.create = self.create.replace("<TABLE_NAME>", name)
        self.drop = self.drop.replace("<TABLE_NAME>", name)
        self.insert = self.insert.replace("<TABLE_NAME>", name)
        self.delete = self.delete.replace("<TABLE_NAME>", name)


class Ora11gR2(TableSQL):

    """Tables of Oracle whose version is 11gR2."""

    class Meta:
        verbose_name = "Oracle 11G R2 table sql"
        verbose_name_plural = "Oracle 11G R2 table sqls"
