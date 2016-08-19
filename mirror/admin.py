# coding:utf-8
from django.contrib import admin
from mirror.models import *


@admin.register(GlobalConfig, RedisServer, MySQLServer, OracleTarget)
class BasicAdmin(admin.ModelAdmin):

    """Admin for Models who want's to display simple list."""

    list_display = ('id', 'name', 'enable', 'desc')


@admin.register(Ora11gR2)
class TableSQLAdmin(admin.ModelAdmin):

    """Admin for TableSQL Models,Notice that TableSQL is an abstract base class."""

    list_display = ('id', 'name', 'enable', 'desc', 'period')

    fieldsets = (
        (
            None,{
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
                    1，添加新表前一定要先测试，测试成功后再确认添加！
                    <br>
                    2，SQL语句的结尾不要添加分号！
                    <br>
                    3，特殊字符#尽量去掉！
                    <br>
                    4，用&lt;TABLE_NAME&gt;来代替不确定的表名！
                    <br>
                    5，Create语句必须加上 'if not exists'！
                    <br>
                    6，Create必须加上 'ENGINE = MEMORY！'！
                    <br>
                    7，Oracle中的Number类型，对应MySQL中的Bigint类型！
                    <br>
                    8，Insert中数据的值，必须使用%s来表示，不需要%d之类的！
                """,
                'fields': ('create', 'drop', 'insert', 'delete')
            }
        )
    )