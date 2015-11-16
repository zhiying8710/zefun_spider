# coding: utf-8

import redis
import traceback
from zefun_spider.settings import redis_df_db, redis_host, redis_port

class RedisHelper():

    @staticmethod
    def get_redis_conn(db=redis_df_db):
        return redis.Redis(host=redis_host, port=redis_port, db=db)

    @staticmethod
    def close_redis_conn(rconn):
        if rconn:
            del rconn

def redis_exec(rconn):
    def wrapper(fn):
        def _exec(*args, **kwargs):
            try:
                return fn(rconn = rconn, *args, **kwargs)
            except:
                raise Exception(traceback.format_exc())
            finally:
                RedisHelper.close_redis_conn(rconn)
        return _exec
    return wrapper
