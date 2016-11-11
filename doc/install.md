######### Others ################
MySQL database - utf-8
Redis


######### Common ################

[Python Environment Manager]

pyenv

[Python modules]

Python==2.7.11+
Pip
#Cython==0.24.1
Django==1.9.7
gunicorn
supervisor==3.3.1

cx_Oracle==5.2.1
MySQL-python==1.2.5
redis
influxdb

celery==3.1.24
pytz # pre for APScheduler
APScheduler==3.2.0

######### Ubuntu ################

[Oracle Instant Client]

oracle-instantclient11.2-basic_11.2.0.4.0-2_amd64.deb
oracle-instantclient11.2-devel_11.2.0.4.0-2_amd64.deb
oracle-instantclient11.2-sqlplus_11.2.0.4.0-2_amd64.deb


[Influxdata TICK stack]

telegraf_0.13.2_amd64.deb
chronograf_0.13.0_amd64.deb
kapacitor_0.13.1_amd64.deb
influxdb_0.13.0_amd64.deb

######### Redhat ################

[Oracle Instant Client]

oracle-instantclient11.2-basic-11.2.0.4.0-1.x86_64.rpm
oracle-instantclient11.2-devel-11.2.0.4.0-1.x86_64.rpm
oracle-instantclient11.2-sqlplus-11.2.0.4.0-1.x86_64.rpm

[Influxdata TICK stack]

chronograf-0.13.0-1.x86_64.rpm
influxdb-0.13.0.x86_64.rpm
kapacitor-0.13.1.x86_64.rpm
telegraf-0.13.1.x86_64.rpm
