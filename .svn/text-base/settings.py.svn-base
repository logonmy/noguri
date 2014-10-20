# -*- coding:utf-8 -*-
import redis
from redis.connection import BlockingConnectionPool
from socket_log import initlog

# ------------ 状态转发服务器 ------------
STATUS_SERVER = '10.2.161.15'

PORT = 8022

# ------------ redis 相关配置 ------------
REDIS_HOST = '10.2.161.15'

REDIS_PORT = 6379

REDIS_DB_NUM = 1

REDIS_PASSWORD = 'N6MXWf'

# ------------- 连接池 --------------- 
# redis数据库
# 阻塞式连接池
pool = BlockingConnectionPool(max_connections=20, timeout=5, socket_timeout=5, \
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_NUM, password=REDIS_PASSWORD)
REDIS_DB = redis.StrictRedis(connection_pool=pool)

# -------------- 日志接收服务器 ---------

LOG_HOST = 'localhost'

LOG_PORT = 9030


# ------------ 初始化　日志记录器　------------
initlog('task.generator', LOG_HOST, LOG_PORT)











