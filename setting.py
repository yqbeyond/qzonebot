# coding: utf-8

from __future__ import unicode_literals

DB_NAME = "qzone"

# 客户代理，这里默认使用Chrome。
Agent = {
    'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
}

# QQ 账号配置
# QQ账号
# QQ密码
# 还是二维码安全，暂时没写账号、密码、登录的方法。

# 数据库配置 (Mysql中途已放弃，存储对象太不方便了)
# db_host = localhost
# db_port = 3306
# db_user = root
# db_passwd = 123456
# db_name = QZONE
# charset = utf8
# use_unicode = True

# [mongodb]
# 使用默认

# 保存cookie, 如果有从qzone.pkl读入（没写）
# cookie = qzone.pkl

# 同时爬取线程数（没写）
# thread_amount = 2
