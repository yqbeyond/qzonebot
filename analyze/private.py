"""
对一个好友进行数据分析
"""

import time
import pymongo
import matplotlib.pyplot as plt
from pymongo import MongoClient


dbclient = MongoClient()
coll = dbclient.qzone.moods

def private_time_analyze(uin):
    moods_time = coll.find({'uin': uin}, {"_id": 0, "created_time": 1})
    timestamps = [mood_time['created_time'] for mood_time in moods_time]
    counts = [0 for i in range(24)]
    for timestamp in timestamps:
        counts[time.localtime(timestamp).tm_hour] += 1
    hours = list(range(24))

    fig, ax = plt.subplots()
    ax.plot(hours, counts, 'o-')
    ax.set_xlim(0, 24)
    ax.set_xticks([i for i in range(24)])
    ax.set_xticklabels([str(i)+":00" for i in range(24)])
    plt.title(str(uin) +"'s mood time table")
    plt.xlabel("time(s)")
    plt.ylabel("frequency")
    for i in range(24):
        plt.text(hours[i]+ 0.2, counts[i], str(counts[i]))
    fig.set_size_inches(13.5, 8.5)
    fig.savefig(str(uin))
