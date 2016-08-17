from django.contrib import admin
from orm.models import *


class GlobalConfigsAdmin(admin.ModelAdmin):

    """Admin for GlobalConfigs Model"""

    list_display=('id','name','value','desc')


class DBConfigsAdmin(admin.ModelAdmin):

    """Admin for DBConfigs Model"""

    list_display=('id','name','enable','desc')


class PullTablesAdmin(admin.ModelAdmin):

    """Admin for PullTables Models,Notice that PullTables is not a model."""

    list_display=('id','name','period','desc')


# Register your models here.


# Basic models here

admin.site.register(GlobalConfigs,GlobalConfigsAdmin)
admin.site.register(DBConfigs,DBConfigsAdmin)

# Pull tables here

admin.site.register(PTOra11gR2,PullTablesAdmin)

# Pick tables here

pass