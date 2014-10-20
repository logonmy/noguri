# -*- coding:utf-8 -*-
# python 版的 DelayQueue 类 和 Delayed 接口　
# 
from Queue import PriorityQueue
from datetime import datetime
import threading

class Delayed(object):
    # 返回:计划执行时间
    # 单位: datetime
    def plan_time(self):
        pass
        
def total_seconds(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
     

class DelayQueue(PriorityQueue):
    def _init(self, maxsize):
        self.queue = []
        # 如果任务没有到达执行时间，则消费者必须等待在此condition上
        self.lock = threading.Lock()
        self.can_done = threading.Condition(self.lock)
     
    def put_task(self, task):
        self.put((task.plan_time, task))

    # 检索并移除此队列的头部，如果此队列不存在未到期延迟的元素，则等待它 
    def take_task(self):
        self.can_done.acquire()
        try:
            task = self.peek()
            delta = total_seconds(task.plan_time - datetime.now())
            while delta > 0:
                self.can_done.wait(delta)
                
                task = self.peek()
                delta = total_seconds(task.plan_time - datetime.now())

            item = self.get()
            self.can_done.notify_all()
            return item[1]
        finally:
            self.can_done.release()
        
    def peek(self):
        self.not_empty.acquire()
        try:
            while not self._qsize():
                self.not_empty.wait()
            
            return self.queue[0][1]
        finally:
            self.not_empty.release()
            
            


        
        
        
        
        
        
        
        
        
        
        