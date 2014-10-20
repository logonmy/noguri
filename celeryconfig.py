# -*- coding:utf-8 -*-
from settings import REDIS_PASSWORD, REDIS_HOST
from settings import REDIS_PORT, REDIS_DB_NUM

# 某个程序中出现的队列，在broker中不存在，则立刻创建它
CELERY_CREATE_MISSING_QUEUES = True

CELERY_IMPORTS = ("async_task.tasks",)

# 使用redis 作为任务队列
BROKER_URL = 'redis://:' + REDIS_PASSWORD + '@' + REDIS_HOST + ':' + str(REDIS_PORT) + '/' + str(REDIS_DB_NUM)

# 执行结果(执行结果无用)
# CELERY_RESULT_BACKEND = 'redis://:' + REDIS_PASSWORD + '@' + REDIS_HOST + ':' + str(REDIS_PORT) + '/2' 

CELERY_TIMEZONE = 'Asia/Shanghai'

################################################
# 启动worker的命令
# 请切换到venus目录下再执行以下命令
# 消费短信发送任务
# nohup celery worker -f /var/log/noguri/celery.log -l INFO --concurrency=4 --queues=_check_task &
################################################