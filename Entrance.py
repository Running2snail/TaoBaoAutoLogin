# -*- coding:UTF-8 -*-
import time
# import subprocess
import os
from apscheduler.schedulers.blocking import BlockingScheduler


def everyday_crawler_job():
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    os.system("python Crawler.py")

sched = BlockingScheduler()
#每隔一天 执行抓包程序
# sched.add_job(everyday_crawler_job, 'interval', seconds=30)
#每天早上八点半和十二点半各执行一次抓包程序
sched.add_job(everyday_crawler_job, 'cron', coalesce=True, misfire_grace_time=30, hour='8,12', minute='30')
sched.start()





