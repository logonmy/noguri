# -*- coding:utf-8 -*-
##############################
# 公共类
##############################
import time
import random
from datetime import datetime, timedelta
from delay_queue import Delayed
from threading import Thread, Event

class CheckTask(Delayed):
    def __init__(self, appname, host, check_interval):
        self.appname = appname
        self.host = host
        delay_time = random.randint(0, check_interval * 60 * 1000)
        delay_time = float(delay_time) / 1000
        self.plan_time = datetime.now() + timedelta(seconds=delay_time)
        
    def cycle_clone(self, check_interval):
        task = CheckTask(self.appname, self.host, check_interval)
        task.plan_time = self.plan_time + timedelta(seconds=check_interval * 60)
        return task
        
    def plan_time(self):
        return self.plan_time
        
    def __unicode__(self):
        return u"检查任务--应用:%s,主机:%s,计划执行时间:%s" % (self.appname,
            self.host, self.plan_time.strftime('%Y-%m-%d %H:%M:%S'))
            
            
class LoopTimer(Thread):
    """重写了Threading.Timer 类,以定时循环执行"""
    # interval    --单位:秒
    def __init__(self, interval,function, args=[], kwargs={}):
        Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.finished = Event()

    def cancel(self):
        """停止定时器"""
        self.finished.set()

    def run(self):
        # 随机休眠一段时间, 再开始循环
        t = random.randint(0, self.interval)
        time.sleep(t)
        while not self.finished.is_set():
            self.finished.wait(self.interval)
            if not self.finished.is_set():
                self.function(*self.args, **self.kwargs)
