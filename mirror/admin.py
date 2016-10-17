# coding:utf-8
from django.contrib import admin
from mirror.models import *


@admin.register(GlobalConfig, RedisServer, MySQLServer)
class BasicAdmin(admin.ModelAdmin):

    """Admin for Models who want's to display simple list."""

    list_display = ('id', 'name', 'enable', 'desc')


@admin.register(OracleTarget)
class OracleTargetAdmin(admin.ModelAdmin):

    list_display = ('id', 'name', 'enable', 'desc')

    fieldsets = (
        (
            'Basic', {
                'fields': ('name', 'enable', 'desc')
            }
        ), (
            'Verify Check', {
                'fields': ('version', 'rac', 'dbid', 'instance')
            }
        ), (
            'Connection Information', {
                'fields': ('host', 'port', 'user', 'password', 'service')
            }
        ), (
            'Relations', {
                'fields': ('table_collection', 'mysql_server', 'mysql_db', 'redis_server', 'redis_db')
            }
        )
    )


@admin.register(Ora11gR2)
class TableSQLAdmin(admin.ModelAdmin):  # todo : restart proxy, it will effect.

    """Admin for TableCollections Models,Notice that TableCollections is an abstract base class."""

    list_display = ('id', 'name', 'enable', 'desc', 'period')

    fieldsets = (
        (
            'Basic', {
                'fields': ('name', 'enable', 'desc', 'period')
            }
        ), (
            'Pull SQL in Target Oracle Database', {
                'description': """
                    1，SQL语句的结尾不要添加分号！
                """,
                'fields': ('pull',)
            }
        ), (
            'Cache SQL in MySQL Server', {
                'description': """
                    <h1> Please Notice That: </h1>

                    <h3> First At All </h3>
                    <ol> 1，添加新表前一定要先测试，测试成功后再确认添加！ </ol>

                    <h3> Special Sign Notice </h3>
                    <ol> 1，SQL语句的结尾不要添加分号 ';' ！ </ol>
                    <ol> 2，MySQL中特殊字符 '#' 尽量去掉！ </ol>

                    <h3> Create SQL Syntax </h3>
                    <ol> 1，Create语句中Oracle中的Number类型，对应MySQL中的Bigint类型！ </ol>
                    <ol> 2，Create语句必须加上 'if not exists'！ </ol>
                    <ol> 3，Create必须加上 'ENGINE = MEMORY！'！ </ol>

                    <h3> Insert SQL Syntax </h3>
                    <ol> 1，Insert中数据的值，必须使用%s来表示，不需要%d之类的！ </ol>

                    <h3> Drop SQL Syntax </h3>
                    <ol> 1，Drop语句必须加上 'if exists'！ </ol>
                """,
                'fields': ('create', 'drop', 'insert', 'delete')
            }
        )
    )