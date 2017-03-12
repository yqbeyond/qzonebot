"""
对所有人分析一下
"""
import time
import numpy as np
import matplotlib.pyplot as plt
from pymongo import MongoClient


dbclient = MongoClient()


def public_time_analyze():
    """
    分析发说说的时间
    """
    coll = dbclient.qzone.moods
    moods_time = coll.find({}, {"_id": 0, "created_time": 1})
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
    plt.title("mood time")
    plt.xlabel("time(s)")
    plt.ylabel("frequency")
    for i in range(24):
        plt.text(hours[i] + 0.2, counts[i], str(counts[i]))
    fig.set_size_inches(13.5, 8.5)
    fig.savefig('public')

def public_gender_analyze():
    """
    性别分布
    """
    coll = dbclient.qzone.profile
    friends_gender = coll.find({}, {'_id': 0, 'sex':1})
    genders = [gender['sex'] for gender in friends_gender]
    counts = [0] * 3 
    for gender in genders:
        counts[gender['sex']] += 1
    labels = ['?', 'male', 'famale']
    explode = (0, 0.1, 0)
    fig, ax = plt.subplots()
    ax.pie(counts, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, startangle=0)
    ax.axis('equal')
    plt.save('gender')

def public_year_analyze():
    """
    每年说说总量走势
    """
    coll = dbclient.qzone.moods
    moods_time = coll.find({}, {"_id":0, "created_time": 1})
    timestamps = [mood_time['created_time'] for mood_time in moods_time]
    years = [time.localtime(timestamp).tm_year for timestamp in timestamps]
    year_list = sorted(set(years))
    counts = [0] * len(year_list)
    start_year = min(year_list)
    for year in years:
        counts[year - start_year] += 1

    fig, ax = plt.subplots()
    ax.bar(year_list, counts)
    plt.xticks(year_list, year_list)
    for i in range(len(year_list)):        
        plt.text(year_list[i] - 0.1 * str(len(year_list)), counts[i], str(counts[i]))
    plt.title("Mood year table")
    plt.xlabel("year(s)")
    plt.ylabel("frequency")
    plt.savefig('year')

    
