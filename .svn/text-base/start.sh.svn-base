#!/bin/bash
PATH=`dirname $0`
# 消费进程数
WORKER_COUNT=4

Start(){
	# 启动检查任务产生器
	/usr/bin/nohup /usr/bin/python $PATH/noguri.py &
	# 启动消费进程数
	/usr/bin/nohup /usr/bin/celery worker -f /var/log/noguri/celery.log -l INFO --concurrency=$WORKER_COUNT --queues=_check_task &
}

Start


