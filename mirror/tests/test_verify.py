from django.test import TestCase

from os import system
import time
from puller.libs import verify
from puller.models import GlobalConfigs
#from puller.datas import globalconfigs_datas as gc_datas

class VerifyTest(TestCase):

    # init for every test,notice that datas inserted will nerver repeat.
    def setUp(self):
        system("service redis start > /dev/null")

        #gc_datas.GlobalConfigsDatas.init()

        #arrays=[('redis_host','localhost','-'),
        #        ('redis_port','6379','-'),
        #        ('redis_db','0','-'),
        #        ('redis_password','','-')]
        #[GlobalConfigs.objects.create(name=n,value=v,desc=d) for n,v,d in arrays]
        #print 'GC datas is :',map(lambda x:x.name,GlobalConfigs.objects.all())


    # test __init__() abnormal
    def test_init_with_config_error(self):
        map(lambda x:x.delete(),GlobalConfigs.objects.all())
        with self.assertRaises(verify.ConfigGetFailed):
            v=verify.Verify()

    # test record() abnormal
    def test_record_with_wrong_passwd(self):
        passwd=GlobalConfigs.objects.get(name="redis_password")
        passwd.value='123'
        passwd.save()
        with self.assertRaises(verify.RedisSaveError):
            v=verify.Verify()
            v.record("hello")

    def test_record_with_redis_stop(self):
        with self.assertRaises(verify.RedisSaveError):
            system("service redis stop > /dev/null")
            v=verify.Verify()
            v.record("hello")

    # test verify() abnormal
    def test_record_with_wrong_passwd(self):
        passwd=GlobalConfigs.objects.get(name="redis_password")
        passwd.value='123'
        passwd.save()
        with self.assertRaises(verify.RedisReadError):
            v=verify.Verify()
            v.verify("hello",1)

    def test_verify_with_redis_stop(self):
        with self.assertRaises(verify.RedisReadError):
            system("service redis stop > /dev/null")
            v=verify.Verify()
            v.verify("hello",1)

    def test_verify_with_null_key(self):
        with self.assertRaises(verify.RedisReadError):
            v=verify.Verify()
            v.verify("hello",1)

    # test function
    def test_record_verify_not_expired(self):
        v1=verify.Verify()
        v1.record("tmptest1")

        time.sleep(1)

        v2=verify.Verify()
        self.assertEquals(v2.verify("tmptest1",2),True)

    def test_record_verify_with_expired(self):
        v1=verify.Verify()
        v1.record("tmptest2")

        time.sleep(2)

        v2=verify.Verify()
        self.assertEquals(v2.verify("tmptest2",1),False)
