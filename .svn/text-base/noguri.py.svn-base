# -*- coding:utf-8 -*-
#############################################
# 应用--主机 检查任务的生成器
#
#############################################
import logging
import threading
from delay_queue import DelayQueue
from settings import REDIS_DB, LOG_HOST, LOG_PORT
from async_task.tasks import check_app
from common import CheckTask, LoopTimer

# 1. 只是简单的取出任务
# 2. 然后往redis中推送一个异步任务 实际的检查动作由celery 完成
# 3. 根据检查间隔，创建一个新的任务推送到队列中
   
class Generator(threading.Thread):
    def __init__(self, queue, config_dict):
        threading.Thread.__init__(self)
        self.queue = queue
        self.config_dict = config_dict
        
    def run(self):
        logger = logging.getLogger("task.generator")
        while True:
            try:
                # 1.取出任务
                task = self.queue.take_task()
                
                # 2.redis中推送一个异步任务
                check_app.apply_async((task,), queue='_check_task')
                logger.info(u'【获取任务】%s,推送至redis.', unicode(task))
                self.queue.task_done()
                
                # 3.判断是否还要周期性的检查
                item = self.config_dict.get(task.appname)
                if item:
                    host_list = item['host_list']
                    check_interval = int(item['check_interval'])
                    host_list = host_list.split(',')
                    if task.host in host_list:
                        task = task.cycle_clone(check_interval)
                        self.queue.put_task(task)
                        logger.info(u'【产生新任务】%s,推送至本地队列', unicode(task))
            except BaseException, e:
                logger.info(u'程序异常:%s\n%s', str(e), traceback.format_exc()) 
                
# 获取应用配置
def get_config():
    # 1. 获取应用配置
    app_list_str = REDIS_DB.get('_all_app_list')
    app_list = []
    if app_list_str:
        app_list = app_list_str.split(',')
        
    app_config_dict = {}
    pipe = REDIS_DB.pipeline()
    for appname in app_list:
        pipe.hgetall(appname + '_config')
        
    res_list = pipe.execute()
    for i in range(len(res_list)):
        app_config_dict[app_list[i]] = res_list[i]
        
    return app_config_dict

# 从redis队列中取出多条数据　
def pop_multi(pipeline, key, count):
    for i in range(count):
        pipeline.lpop(key)
        
    item_list = pipeline.execute()
    result_list = []
    for item in item_list:
        if item:
            result_list.append(item)
            
    return result_list

# 更新检查计划
def update_check_plan(app_config_dict, queue):
    logger = logging.getLogger("task.generator")
    
    pipe = REDIS_DB.pipeline()
    change_list = pop_multi(pipe, '_app_change_list', 30)
    logger.info(u'发现应用配置发生变动,应用列表:%s', change_list)
    
    for appname in set(change_list):
        # 获取此应用的最新配置
        new_config = REDIS_DB.hgetall(appname + '_config')
        # 1. 此应用已经被删除了
        if new_config is None:
            
            app_config_dict.pop(appname, None)
            continue
        
        item = app_config_dict.get(appname)
        # 2. 此应用是新添加的应用
        if item is None:
            host_list = new_config['host_list']
            for host in host_list.split(','):
                task = CheckTask(appname, host, int(new_config['check_interval']))
                queue.put_task(task)
                
        else:
            old_host_list = item['host_list'].split(',')
            new_host_list = new_config['host_list'].split(',')
            for host in (set(new_host_list) - set(old_host_list)):
                task = CheckTask(appname, host, int(new_config['check_interval']))
                queue.put_task(task)
        
        # 更新配置    
        app_config_dict[appname] = new_config
        
    
def main():
    # ----------删除原有的所有检查任务----------
    REDIS_DB.delete('_check_task')
    
    # 1. 获取应用配置
    app_config_dict = get_config()
        
    # 2. 初始化任务队列
    queue = DelayQueue()
    
    # 3. 装载任务
    for appname in app_config_dict:
        item = app_config_dict.get(appname)
        if item:
            host_list = item['host_list']
            for host in host_list.split(','):
                task = CheckTask(appname, host, int(item['check_interval']))
                queue.put_task(task)
             
    # 4. 启动消费者
    for i in range(4):
        t = Generator(queue, app_config_dict)
        t.daemon = True
        t.start()
        
    # 5. 更新检查计划(包括添加新的检查任务)
    # 间隔:30秒
    t = LoopTimer(10, update_check_plan, [app_config_dict, queue])
    t.start()
    
    queue.join()   
    
    
    
    
#------------------------- start---------------------------
if __name__ == '__main__':
    main()
    
    
    
    
    
    
    
    
    
    
    