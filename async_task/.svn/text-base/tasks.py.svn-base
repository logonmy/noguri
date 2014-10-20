# -*- coding:utf-8 -*-
#############################
# 执行短信发送
# 需要引入sms_tool中的类
#############################

# standard lib
import re
import time
import httplib
import redis, json
from datetime import datetime, timedelta
import logging, traceback
from celery import task
from urllib import quote
from redis.connection import ConnectionPool, BlockingConnectionPool
from redis.exceptions import RedisError

# our own lib
from settings import REDIS_DB, STATUS_SERVER, PORT
from notify.models import notify_app
from common import CheckTask


# 检查动作
@task
def check_app(task):
    logger = logging.getLogger("task.generator")
    # check_latency -- 比计划的检查时间的延迟值
    check_latency = total_seconds(datetime.now() - task.plan_time)
    
    start_time = time.time()
    (state, info) = _check_app(task)
    end_time = time.time()
    
    # duration -- 检查消耗的时间
    duration = end_time - start_time
    
    # 记录应用状态
    record_app_status(task, state, info, check_latency, duration)
    
    logger.info(u"【处理】检查任务:%s,得出状态:%s,检查延迟:%s 秒,耗时:%s 秒", 
        unicode(task), state, check_latency, duration)
    

# timedelta　对象转换成 秒    
def total_seconds(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
    

def _check_app(task):
    # 访问状态转发服务器获取应用运行状态信息
    app_status = get_status(task.appname, task.host)
    if app_status is None:
        return ('UNKNOW', 'The string of app status is null.')
            
    # 监控
    return monitor(app_status)
    
# 记录应用的状态
def record_app_status(task, status, info, check_latency, duration):
    pipe = REDIS_DB.pipeline()

    # 1. 获取应用的部分配置
    pipe.hget(task.appname + '_config', 'max_check_attempts')
    pipe.hget(task.appname + '_config', 'notify_interval')
    pipe.hget(task.appname + '_config', 'check_interval')
    pipe.hget(task.appname + '_config', 'parent_app_list')
    res_list = pipe.execute()
    
    max_check_attempts = int(res_list[0])
    notify_interval = int(res_list[1])
    check_interval = int(res_list[2])
    parent_app_list = res_list[3]
    
    # 2. 获取上一次状态信息
    key = 'ah_' + task.appname + '_' + task.host
    
    if not REDIS_DB.exists(key):
        pipe.hset(key, 'current_status', 'OK')
        pipe.hset(key, 'status_info', 'OK - ')
        pipe.hset(key, 'current_attempt', 0)
        pipe.hset(key, 'last_state_change', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        pipe.hset(key, 'last_notification', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    pipe.execute()
        
    status_dict = REDIS_DB.hgetall(key)
    current_status = status_dict.pop('current_status')
    current_attempt = status_dict.pop('current_attempt')
    current_attempt = int(current_attempt)
    
    last_state_change = status_dict.pop('last_state_change')
    last_state_change = datetime.strptime(last_state_change, '%Y-%m-%d %H:%M:%S')
    last_notification = status_dict.pop('last_notification')
    last_notification = datetime.strptime(last_notification, '%Y-%m-%d %H:%M:%S')
        
    if current_status != status or status != 'OK':
        current_attempt = current_attempt + 1
        pipe.hset(key, 'current_attempt', current_attempt)
        
        if current_attempt >= max_check_attempts:
            current_status = status
            pipe.hset(key, 'current_status', current_status)
            pipe.hset(key, 'status_info', info)
            pipe.hset(key, 'current_attempt', 0)
            pipe.hset(key, 'last_state_change', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # recovery 事件不受notify_interval影响
            if status == 'OK':
                notify_app.apply_async((task.appname, task.host, 'RECOVERY', status, info))
            margin = total_seconds(datetime.now() - last_notification)
            if status !='OK' and margin > notify_interval * 60:
                pipe.hset(key, 'last_notification', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                notify_app.apply_async((task.appname, task.host, 'PROBLEM', status, info))
                
    else:
        pipe.hset(key, 'current_attempt', 0)
    
    pipe.hset(key, 'duration', duration)
    pipe.hset(key, 'check_latency', check_latency)
    next_scheduled_check = task.plan_time + timedelta(seconds=check_interval * 60)
    next_scheduled_check = next_scheduled_check.strftime('%Y-%m-%d %H:%M:%S')
    pipe.hset(key, 'next_scheduled_check', next_scheduled_check)

    
    # -------- 其它特殊情况 (为了方便判断主机是否存活) ------------
    if parent_app_list is not None:
        if parent_app_list.find('HOST_STATUS') != -1:
            key = 'ah_HOST_STATUS_' + task.host
            pipe.hset(key, 'current_status', current_status)
            
        if parent_app_list.find('SYS_PING') != -1:
            key = 'ah_SYS_PING_' + task.host
            pipe.hset(key, 'current_status', current_status)
    
    pipe.execute()

# monitor value
def monitor(app_status):
    # 是否报警
    warning_flag = False
    critical_flag = False
    
    # 描述信息
    status_info_list = []
    for item in app_status["monitor"]:
        # get monitor records one by one
        value = item["value"]
        warning = item["warning"]
        critical = item["critical"]
        id = item["id"]    
        desc = item["desc"]    
        
        wflag, wnote_str = judge(value, warning)
        cflag, cnote_str = judge(value, critical)
        
        if cflag:
            critical_flag = True
            status_info_list.append(u"id%s=%s CRITICAL"  % (id, desc))
            status_info_list.append(cnote_str)
            
        elif wflag:
            warning_flag = True
            status_info_list.append(u"id%s=%s WARNING"  % (id, desc))
            status_info_list.append(wnote_str)
    
    res = '\n'.join(status_info_list) 
    
    if critical_flag:
        return ('CRITICAL', 'CRITICAL - ' + res )
        
    elif warning_flag:
        return ('WARNING', 'WARNING - ' + res )
        
    else:
        return ('OK', 'OK - ' + res )
        
# parse the threshold from info
def parse_threshold(threshold_str):
    t = None
    t1 = None
    t2 = None
    #mode1-->10: 
    #mode2-->~:10
    #mode3-->10:20
    #mode4-->@10:20
    pattern_list = ['^([\d|\.]+):$','^~:([\d|\.]+)$','^([\d|\.]+):([\d|\.]+)$','^@([\d|\.]+):([\d|\.]+)$']
    for i in range(4):
        res = re.match(pattern_list[i],threshold_str)
        if res is not None:
            if i==0 or i==1:
                t = res.group(1)
                t = float(t)
            else:
                t1 = res.group(1)
                t1 = float(t1)
                
                t2 = res.group(2)
                t2 = float(t2)
            return (i+1,t,t1,t2)
    return None

# judge the value status
def judge(value, threshold_str):
    status = False
    note_str = None
    mode, data, data1, data2 = parse_threshold(threshold_str)
    
    if mode == 1:
        if value < data:
            status = True
    elif mode == 2:
        if value > data:
            status = True
    elif mode == 3:
        if value < data1 or value > data2: 
            status = True
    elif mode == 4:
        if data1 <= value <= data2:
            status = True
            
    if status:
        note_str = note(mode, value, data, data1, data2)
    return status, note_str        
        
        
def get_status(appname, host):
    conn = httplib.HTTPConnection(STATUS_SERVER, PORT, timeout=10)
    appname = quote(appname)
    path = "/monitor/%s/%s" %  (appname, host)
    
    try:
        conn.request("GET", path)
    except BaseException:
        return None
        
    response = conn.getresponse()
    data = response.read()
    
    if len(data) == 0 or response.status != 200:
        return None

    try:
        dd = json.loads(data)
    except BaseException:
        return None
        
    return dd
    
def note(mode, value, data, data1, data2):
    res = u"当前值: " + str(value) + " " 
    if mode == 1:
        res += u"阈值: 当前值 小于" + str(data)
    elif mode == 2:
        res +=  u"阈值: 当前值 大于" + str(data)
    elif mode == 3:
        res +=  u"阈值: 当前值 小于" + str(data1) + u" 或者 当前值 大于" + str(data2)
    elif mode == 4:
        res += u"阈值: 当前值 大于等于" + str(data1) + u" 并且 当前值 小于等于" + str(data2)
    return res
    









    
