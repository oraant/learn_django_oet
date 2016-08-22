import time

import redis

from mirror.models import GlobalConfigs


# verify exceptions
class VerifyException(Exception):
    def __init__(self,value):self.value=value
    def __str__(self):return repr(self.value)
class ConfigGetFailed(VerifyException): pass
class RedisSaveError(VerifyException): pass
class RedisReadError(VerifyException): pass

class Recorder:

    def __init__(self):
        self._connect()

    def _connect(self):
        try:
            host=GlobalConfigs.objects.get(name="redis_host").value
            port=GlobalConfigs.objects.get(name="redis_port").value
            db=GlobalConfigs.objects.get(name="redis_db").value
            password=GlobalConfigs.objects.get(name="redis_password").value
        except Exception,e:
            raise ConfigGetFailed("can't get configs,error is :\n%s\n%s" % (Exception.__class__,e))
        self.conn = redis.Redis(host=host,port=port,password=password,db=db)

    def record(self,name):
        'record with timestamp for the name in redis'
        try:
            self.conn.set(name,time.time())
        except Exception,e:
            raise RedisSaveError("error when record timestamp for %s : %s" % (name,e))

    def verify(self,name,gap):
        try:
            #exists = self.conn.exists(name)
            oldtime=float(self.conn.get(name))
        except Exception,e:
            raise RedisReadError("error when compare timestamp for %s : %s" % (name,e))

        if time.time()-oldtime > gap:
            return False
        return True
