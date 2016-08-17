from django.db import models


# Create your models here.
class GlobalConfigs(models.Model):

    """Global configs with column style."""

    name = models.CharField(max_length=50)
    value = models.CharField(max_length=50, null=True, blank=True)
    desc = models.CharField(max_length=300)


class DBConfigs(models.Model):

    """Targets oracle database you want to monitor."""

    name = models.CharField(max_length=30)
    enable = models.BooleanField(default=True)
    desc = models.CharField(max_length=300)

    version = models.CharField(max_length=30)
    rac = models.BooleanField(default=False)
    dbid = models.CharField(max_length=30)
    instance = models.IntegerField()

    ip = models.CharField(max_length=30)
    port = models.CharField(max_length=30)
    user = models.CharField(max_length=30)
    password = models.CharField(max_length=30)
    service = models.CharField(max_length=30)

    tables = models.CharField(max_length=30)
    points = models.CharField(max_length=30)


class PTOra11gR2(models.Model):

    """Target tables you want to mirror to server who's Oracle version is 11gR2."""

    name = models.CharField(max_length=30)
    enable = models.BooleanField(default=True)
    desc = models.CharField(max_length=300)
    period = models.IntegerField()

    pull = models.CharField(max_length=900)
    create = models.CharField(max_length=900)
    drop = models.CharField(max_length=900)
    insert = models.CharField(max_length=900)
    delete = models.CharField(max_length=900)
