# coding: utf-8

import os, sys
import requests
import random
import time
import re
import json
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
from setting import Agent, DB_NAME
from utils import jscallback2dict
from pymongo import MongoClient


class Client(object):
    def __init__(self):

        # 下面的URL包含`&&`,用字典构造参数失败。直接贴上来了。
        url = 'http://xui.ptlogin2.qq.com/cgi-bin/xlogin?proxy_url=http%3A//qzs.qq.com/qzone/v6/portal/proxy.html&daid=5&&hide_title_bar=1&low_login=0&qlogin_auto_login=1&no_verifyimg=1&link_target=blank&appid=549000912&style=22&target=self&s_url=http%3A%2F%2Fqzs.qzone.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone&pt_qr_app=%E6%89%8B%E6%9C%BAQQ%E7%A9%BA%E9%97%B4&pt_qr_link=http%3A//z.qzone.com/download.html&self_regurl=http%3A//qzs.qq.com/qzone/v6/reg/index.html&pt_qr_help_link=http%3A//z.qzone.com/download.html'
        self.session = requests.Session()
        self.session.get(url)  # 获取一些Cookie
        self.uin = None
        self.qzonetoken = None  # QQ空间令牌
        self.g_tk = None  # 不知道是什么令牌
        self.dbclient = MongoClient()
        self.db = self.dbclient[DB_NAME]

    def check_login(self):
        """
        :return: 成功返回 ptsigx（二维码唯一标志，用于登录）
        """
        url = 'http://ptlogin2.qq.com/ptqrlogin?u1=http%3A%2F%2Fqzs.qzone.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone&ptqrtoken=' + str(self.ptqrtoken(self.session.cookies.get("qrsig"))) +'&ptredirect=0&h=1&t=1&g=1&from_ui=1&ptlang=2052&action=0-0-1488985645380&js_ver=10201&js_type=1&login_sig='+ self.session.cookies.get('pt_login_sig') + '&pt_uistyle=40&aid=549000912&daid=5&'
        rep = self.session.get(url)
        if self.session.cookies.get('uin'):
            self.uin = self.session.cookies.get('uin')[2:]
            content = rep.content.decode('utf-8')
            pattern = re.split(r'&', content)
            return pattern[4].split('=')[1]
        else:
            return False

    def ptqrtoken(self, qrsig):
        """
        :param str | qrsig: 二维码标志
        :return int | ptqrtoken: 根据qrsig返回ptqrtoken。二维码有效期内有效（好像是2两分钟）
        """
        token = 0
        for i in range(len(qrsig)):
            token += (token << 5) + ord(qrsig[i])
        return token & (2 ** 31 - 1)

    def set_g_tk(self):
        """
        :return: 不知道这个g_tk是个什么令牌，反正后面常用
        """
        token = 5381
        p_skey = self.session.cookies.get('p_skey')
        for i in range(len(p_skey)):
            token += (token << 5) + ord(p_skey[i])            
        self.g_tk = token & (2**31 - 1)
        return self.g_tk    

    def login(self):
        time_count = 0
        self.get_qr()
        print("Please scan the QR code to login in ...")
        while True:
            ptsigx = self.check_login() # 用于检测登录状态
            if ptsigx:
                url = "http://ptlogin4.qzone.qq.com/check_sig?pttype=1&uin=584350987&service=ptqrlogin&nodirect=0&ptsigx=" + ptsigx + "&s_url=http%3A%2F%2Fqzs.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone&f_url=&ptlang=2052&ptredirect=100&aid=549000912&daid=5&j_later=0&low_login_hour=0&regmaster=0&pt_login_type=3&pt_aid=0&pt_aaid=16&pt_light=0&pt_3rd_aid=0"
                self.session.get(url, headers=Agent)
                self.set_qzonetoken()
                self.set_g_tk()
                print('Login Successfully.')
                print('Hello, ' + self.session.cookies.get('uin')[2:])
                break
            else:                
                if (time_count >= 120000): # 两分钟后自动获取二维码
                    print("QR code has out of date, loading new ...")
                    print("Please scan the QR code to login ...")
                    self.get_qr()
                    time_count = 0
                else:
                    time.sleep(0.3)
                    time_count += 300

    def set_qzonetoken(self):
        """
        设置 qzonetotken
        """
        if not self.qzonetoken:
            script = self.get_qzonetoke_code()
            token = input("(•_•)\n" +"<) )> 请将下面奇怪的代码复制到浏览器控制台执行，将结果粘贴到光标处输入..." + "\n/ \\\n\n" + script + "\nInput: ")
            self.qzonetoken = token

    def get_qzonetoke_code(self):
        """
        解析出用于生成qzonetoken的JS脚本。
        说明：测试了一些JS脚本执行环境的库会产生LocationError。不会JS，不明所以。
        :return str | script: 用于生成qzonetoken的JS脚本
        """
        url = "https://user.qzone.qq.com/" + self.session.cookies.get('uin')[2:]
        rep = self.session.get(url, headers = Agent)
        htmlparser = BeautifulSoup(rep.text, 'lxml')
        script = htmlparser.find_all('script')[-1].text
        pattern = re.split(r' ', script)
        return pattern[4][:-2]

    def get_qr(self):
        """
        下载登录用的二维码并打开。
        """
        QR_URL = 'http://ptlogin2.qq.com/ptqrshow'
        params = {
            'appid': '549000912',
            'e': '2',
            'l': 'M',
            's': '3',
            'd': '72',
            'v': '4',
            't': random.random(),
            'daid': '5',
        }
        print("Downloading QR code ...")
        rep = self.session.get(QR_URL, params=params)
        if rep.status_code == 200:
            qrimg = Image.open(BytesIO(rep.content))
            qrimg = qrimg.resize((qrimg.size[0]*2, qrimg.size[1]*2))
            qrimg.save('qrcode.png', format='png')
            print("loading QR code ...")
            if sys.platform == 'linux':
                os.system('xdg-open qrcode.png')
            else:
                print("QR Code has been download, please open it and scan.")

    def get_friends(self):
        """
        :return response: 包含好友列表的Response对象
        """

        if not self.qzonetoken:
            self.set_qzonetoken()

        params = {
            'uin': self.session.cookies.get('uin')[2:],
            'do': 1,
            'rd': random.random(),
            'fupdate': 1,
            'clean': 1,
            'g_tk': self.g_tk,
            'qzonetoke': self.qzonetoken,
        }
        url = "https://h5.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/tfriend/friend_ship_manager.cgi"
        rep = self.session.get(url, headers=Agent, params=params)
        return rep

    def crawl_friendship(self):
        """
        爬取好友关系，将其存入friendship集合。
        :return:
        """
        print("Crawling friendship ...")
        rep = self.get_friends()
        data = json.loads(jscallback2dict(rep.text))
        data = data["data"]
        data["timestamp"] = int(time.time())
        self.db.friendship.insert_one(data)  # try一下
        print("Insert friendship successfully at " + time.strftime("%Y-%m-%d %H:%M:%D", time.localtime(data['timestamp'])))

    def get_info(self, uin):
        """
        获取一个好友的个人档
        :param int | uin: 好友账号
        :return: 包含好友个人档的Response对象
        """
        profile_url = "https://h5.qzone.qq.com/proxy/domain/base.qzone.qq.com/cgi-bin/user/cgi_userinfo_get_all"
        params = {
            "uin": uin,
            "vuin": self.uin,
            "fupdate": 1,
            "rd": random.random(),
            "g_tk": self.g_tk,
        }
        rep = self.session.get(profile_url, params=params, headers=Agent)
        return rep

    def crawl_info(self, uin):
        """
        爬取一个好友的个人档存入profile集合
        :param int | uin : 好友账号
        """
        try:
            rep = self.get_info(uin)
            data = json.loads(jscallback2dict(rep.text))
            if data.get('code') == 0:
                data = data['data']
                res = self.db.profile.insert_one(data).inserted_id
                print("Insert uin " + str(uin) + " profile successfully with inserted id " + str(res))
            else:
                print(str(uin), data.get('code'), data.get('message'))
        except json.JSONDecodeError as err:
            print(err)

    def get_plcount(self, uin):
        """
        获取一个好友的说说、日志、相片、留言数量等
        :param int | uin: 好友账号
        :return: 包含好友空间上述信息的Response对象
        """
        plcount_url = "https://h5.qzone.qq.com/proxy/domain/snsapp.qzone.qq.com/cgi-bin/qzonenext/getplcount.cgi"
        params = {
            'hostuin': uin,
            'g_tk': self.g_tk,
        }
        rep = self.session.get(plcount_url, headers=Agent, params=params)
        return rep

    def crawl_plcount(self, uin):
        """
        爬取一个好友的空间说说、相册、相片、留言数量存入plcount集合
        :param into | uin : 好友账号
        :return: 包含好友上诉信息的Response对象
        """
        print("Crawl uin " + str(uin) + "'s plcount ...")

        rep = self.get_plcount(uin)
        data = json.loads(jscallback2dict(rep.text))
        if data.get('result').get('code') == 0:
            data['uin'] = uin
            self.db.plcount.insert_one(data)
            print("Insert uin " + str(uin) + "'s plcount successfully.")
        else:
            print(str(uin), data['code'], data['message'])

    def crawl_all_plcount(self):
        """
        获取所有好友的说说数目，日志数目、相册数目等。
        :return:
        """
        print("Crawling all frineds' plcount ...")
        uins = self.get_uins()
        for uin in uins:
            self.crawl_plcount(uin)
        print("Plcount crawling done.")

    def get_mood(self, uin, pos, num):
        """
        获取一条说说。（如果没有获取到指定num的说说，会漏抓）
        :param int | uin: 好友账号
        :param int | pos: 起始位置
        :param int | num: 抓取数目（40以下）
        :return: 包含说说的对象
        """
        mood_url = "https://h5.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6"
        params = {
            'uin': uin,
            'inCharset': 'utf-8',
            'outCharset': 'utf-8',
            'hostUin': uin,
            'notice': 0,
            'sort': 0,
            'pos': pos,  # 从上次截断的地方开始
            'num': num,  # 请求的说说数目
            'cgi_host': 'http://taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6',
            'code_version': 1,
            'format': 'jsonp',
            'need_private_comment': 1,
            'g_tk': self.g_tk,
        }
        rep = self.session.get(mood_url, headers=Agent, params=params)
        return rep

    def crawl_mood(self, uin):
        """
        爬取某个好友的所有说说存入moods数据库
        :param int | uin: 好友账号
        """
        rep = self.get_mood(uin=uin, pos=0, num=1)  # 测试是否被屏蔽
        data = json.loads(jscallback2dict(rep.text))
        if data.get('code') == 0:
            coll = self.db.plcount
            res = coll.find_one({"uin": uin})
            SS = res.get('count').get('SS')
            if not SS:
                return
            num = 40  # 一次返回的说说数目
            pos = 0
            count = 0
            coll = coll.db.moods
            print("Crawl uin " + str(uin) + "'s moods ...")
            while count < SS:
                rep = self.get_mood(uin=uin, pos=pos, num=num)
                data = json.loads(jscallback2dict(rep.text))
                if data.get('msglist'):
                    coll.insert_many(data['msglist'])
                    print("Successfully insert %d moods" % len(data['msglist']))
                    pos += num
                    count += num
                else:
                    print("no moods crawled: " + str(uin))
                    break
        else:
            print(str(uin), data['code'], data['message'])

    def crawl_all_mood(self):
        """
        抓取所有好友的所有说说存入moods集合
        """
        print("Crawling all friends' moods ...")
        uins = self.get_uins()
        for uin in uins:
            self.crawl_mood(uin)
        print("Moods crawling done.")

    def get_opcnt(self, uin, unikey, face):
        """
        获取好友每条说说的点赞数、转发数等（没具体写，这个函数不能用）
        :param int | uin: 好友账号
        """
        pass
        """
        opcnt_url = 'https://h5.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/user/qz_opcnt2'
        params = {
            '_stp': int(time.time()*1000),
            'unikey': unikey,  # 各个mood的链接
            'face': face,  # 分割用
            'fupdate': 1,
            'g_tk': self.g_tk,
        }
        rep = self.session.get(url, headers=Agent, params=params)
        """

    def crawl_opcnt(self, uin):
        """
        爬取一个好友所有说说的点赞数、转发数等（没具体写，此函数不能用）
        :param int | uin: 好友账号
        """
        """
        print("Crawling uin " + uin + "'s opcnt ...")
        rep = self.get_opcnt(uin, unikey, face)
        data = json.loads(jscallback2dict(rep.text))
        data = data['data']
        data = data.values()
        data['uin'] = uin
        res = self.db.opcnt.insert_one(data).inserted_id
        print("Insert uin + " + str(uin) + " opcnt successfully with inserted id" + str(res))
        """

    def get_message_board(self, uin, start, num):
        """
        获取留言，返回包含留言信息的对象
        :param int | uin: 好友账号
        :param int | start: 起始位置
        :param int | num: 抓取数量（15左右）
        :return:
        """

        message_board_url = "https://h5.qzone.qq.com/proxy/domain/m.qzone.qq.com/cgi-bin/new/get_msgb"
        params = {
            "uin": self.uin,
            "hostUin": uin,
            "num": num,
            "start": start,
            "hostword": 0,
            "essence": 1,
            "r": random.random(),
            "iNotice": 0,
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "format": "jsonp",
            "ref": "qzone",
            "g_tk": self.g_tk,
            "qzonetoken": self.qzonetoken,
        }
        rep = self.session.get(message_board_url, headers=Agent, params=params)
        return rep

    def crawl_message_board(self, uin):
        """
        爬取好友的留言板
        :param uin:
        :return:
        """
        rep = self.get_message_board(uin, start=0, num=1)  #测试是否被屏蔽
        data = json.loads(jscallback2dict(rep.text))
        if data.get('code') == 0:
            coll = self.db.plcount
            res = coll.find_one({"uin": uin})
            LY = res.get("count").get("LY")
            if not LY:
                return
            num = 20
            start = 0
            count = 0
            coll = self.db.message_boards
            print("Crawling uin " + str(uin) + "'s message board ...")
            while count < LY:
                rep = self.get_message_board(uin=uin, start=start, num=num)
                data = json.loads(jscallback2dict(rep.text))

                for i in range(len(data['data']['commentList'])):
                    data['data']['commentList'][i]['hostUin'] = uin

                coll.insert_many(data['data']['commentList'])
                # coll.update({"uin": uin}, {"$addToSet": {"msgList": {"$each": data['data']['commentList']}}})
                print("Successfully insert %d message " % len(data['data']['commentList']))
                start += num
                count += num
        else:
            print(str(uin), data.get('code'), data.get('message'))

    def crawl_all_message(self):
        """
        抓取所有好友的留言存入message_borad集合。
        """
        print("Crawling all friends' message board ...")
        uins = self.get_uins()
        for uin in uins:
            self.crawl_message_board(uin)
        print("All friends' message board are crawled.")

    def get_blog_info(self, uin, pos, num):
        """
        获取好友指定数目日志的基本信息
        :param int | uin: 好友账号
        :param int | pos: 起始位置
        :param int | num: 数量
        :return: 包含日志基本信息的Response对象
        """
        blog_info_url = "https://h5.qzone.qq.com/proxy/domain/b11.qzone.qq.com/cgi-bin/blognew/get_abs"
        params = {
            "hostUin": uin,
            "uin": self.uin,
            "blogType": 0,
            "cateName": "",
            "cateHex": "",
            "statYear": "",
            "reqInfo": 1,
            "pos": pos,
            "num": num,
            "sortType": 0,
            "absType": 0,
            "source": 0,
            "rand": time.time(),
            "ref": "qzone",
            "g_tk": self.g_tk,
            "verbose": 0,
            "iNotice": 0,
            "inCharset": "gbk",
            "outCharset": "gbk",
            "format": "jsonp",
            "qzonetoken": self.qzonetoken,
        }

        rep = self.session.get(blog_info_url, headers=Agent, params=params)
        return rep

    def get_blog_content(self, uin, blogid):
        """
        获取好友的日志内容。
        :param int | uin: 好友账号
        :param int | blogid: 博客账号
        :return str: 博客内容
        """

        content_url = "http://b11.qzone.qq.com/cgi-bin/blognew/blog_output_data"
        params = {
            "uin": uin,
            "blogid": blogid,
            "styledm": "qzonestyle.gtimg.cn",
            "imgdm": "qzs.qq.com",
            "bdm": "b.qzone.qq.com",
            "mode": 2,
            "numperpage": 15,
            "timestamp": int(time.time()),
            "dprefix": "",
            "inCharset": "gb2312",
            "outCharset": "gb2312",
            "ref": "qzone",
            "refererurl": "http://qzs.qq.com/qzone/app/blog/v6/bloglist.html#nojump=1&page=1&catalog=list",
        }
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Host': 'b11.qzone.qq.com',
            'Pragma': 'no-cache',
            'Referer': 'http://qzs.qq.com/qzone/app/blog/v6/bloglist.html',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        }

        rep = self.session.get(content_url, headers=headers, params=params)
        htmlparser = BeautifulSoup(rep.text, 'lxml')
        content = htmlparser.find("div", attrs={"id": "blogDetailDiv"})
        if content:
            return content.text
        else:
            return "爬取失败"

    def crawl_blog_info(self, uin):
        """
        爬取指定好友的所有日志基本信息
        :param int | uin: 好友账号
        """
        rep = self.get_blog_info(uin, 0, 1)
        data = json.loads(jscallback2dict(rep.text))
        if data.get('code') == 0:
            coll = self.db.plcount
            res = coll.find_one({"uin": uin})
            RZ = res.get("count").get("RZ")
            if not RZ:
                return
            num = 15  # 抓取数量
            pos = 0
            count = 0
            coll = self.db.blogs

            while count < RZ:
                rep = self.get_blog_info(uin, pos, num)
                data = json.loads(jscallback2dict(rep.text))
                for i in range(len(data['data']['list'])):
                    data['data']['list'][i]['hostUin'] = uin

                if data['data']['list']:
                    coll.insert_many(data['data']['list'])
                    print("Successfully insert %d blog infos " % len(data['data']['list']))
                    pos += num
                    count += num
                else:
                    break
        else:
            print(data.get('code'), data.get('message'))

    def crawl_all_blog_info(self):
        """
        爬取所有好友的日志基本信息，存入blogs集合。
        """
        print("Crawling all friends' blog info ...")
        uins = self.get_uins()
        for uin in uins:
            self.crawl_blog_info(uin)
        print("All friends' blog info are crawled.")

    def crawl_blog(self, uin):
        """
        爬取指定好友的所有日志，存入blogs集合。
        :param uin:
        """
        coll = self.db.blogs
        blog_infos = coll.find({"hostUin": uin})
        if not blog_infos:
            return
        blog_ids = [blog_info['blogId'] for blog_info in blog_infos]

        for blog_id in blog_ids:
            print("Updateing ", uin, blog_id, "...")
            content = self.get_blog_content(uin, blog_id)
            coll.update({"hostUin": uin, "blogId": blog_id}, {"$set": {"content": content}})

    def crawl_all_blog(self):
        """
        爬取所有好友的所有日志。
        特别说明：抓太多会被封号。
        """
        print("Crawling all friends blogs ...")
        uins = self.get_uins()
        for uin in uins:
            self.crawl_blog(uin)
        print("All friends' blog are crawled.")


    def get_album_info(self, uin):
        """
        没有实现
        :param uin:
        :return:
        """
        pass
        """
        album_info_url = 'https://h5.qzone.qq.com/proxy/domain/ic2.qzone.qq.com/cgi-bin/feeds/feeds2_html_picfeed_qqtab'
        params = {
            'appid': 4,
            'notice': 0,
            'hostUin': uin,
            'inCharset': 'utf-8',
            'outCharset': 'utf-8',
            'format': 'jsonp',
            'source': 'qqinfotab',
            'plat': 'qzone',
            'uin': self.uin,
            'list': 1,
            'contain': 0,
            'refer': 'qqinfotab',
            'fuin': 'uin',
            'g_tk': self.g_tk,
        }
        rep = self.session.get(album_info_url, headers=Agent, params=params)
        return rep
        """

    def crawl_album_info(self, uin):
        """
        没有实现
        :param uin:
        :return:
        """
        pass
        """
        print("Crawling uin " + uin + "'s album info ... ")
        rep = self.get_album_info(uin)
        data = json.loads(jscallback2dict(rep.text))
        data = data['data']
        data['uin'] = uin
        res = self.db.ablum_info.insert_one(data).inserted_id
        print("Insert uin + " + str(uin) + " album info successfully with inserted id" + str(res))
        """

    def get_uins(self):
        """
        返回一个包含所有好友uin的列表, 前提是数据库中已经存有好友的信息
        :return list | uins: 包含所有好友账号的列表
        """
        coll = self.db.friendship
        res = coll.find_one()
        users = [user['uin'] for user in res['items_list']]
        return users

    def auto_like_one(self, uin, mood_id, like = 1):
        """
        自动为某条说说点赞。
        :param int | uin: 好友账号
        :param str | mood_id: 说说编号
        :param int | like: 1: 点赞， -1: 取消点赞
        :return: 操作结果Response对象
        """
        if like == 1:
            url = "https://h5.qzone.qq.com/proxy/domain/w.qzone.qq.com/cgi-bin/likes/internal_dolike_app"
        else:
            url = "https://h5.qzone.qq.com/proxy/domain/w.qzone.qq.com/cgi-bin/likes/internal_unlike_app"
        params = {
            "g_tk": self.g_tk,
            "qzonetoken": self.qzonetoken,
        }
        data = {
            "qzreferrer": "https://user.qzone.qq.com/" + str(self.uin) + "/?_t_=" + str(random.random),
            "opuin": self.uin,
            "unikey": "http://user.qzone.qq.com/" + str(uin) + "/mood/" + mood_id,
            "curkey": "http://user.qzone.qq.com/" + str(uin) + "/mood/" + mood_id,
            "from": 1,
            "appid": 311,
            "typeid": 0,
            "abstime": int(time.time()),
            "fid": mood_id,
            "active": 0,
            "fupdate": 1,
        }

        rep = self.session.post(url, headers=Agent, data=data, params=params)
        return rep

    def auto_like_all(self, uin, interval=None):
        """
        对某个好友的所有说说点赞。
        特别提示：注意节制，否则会被中断session。
        :param int | uin: 好友账号
        :param int | interval: 每隔多长时间点一次赞。默认不断的点。
        """
        coll = self.db.moods
        moods = coll.find({"uin": uin})
        tids = [mood['tid'] for mood in moods]
        for tid in tids:
            rep = self.auto_like_one(uin, tid, 1)
            print(tid, rep.text)
            if interval:
                time.sleep(interval)

    def auto_leave_msg(self, uin, content):
        """
        给指定好友留言
        :param int | uin: 好友账号
        :return rep: 留言状态Response对象
        """
        url = "https://h5.qzone.qq.com/proxy/domain/m.qzone.qq.com/cgi-bin/new/add_msgb"
        params = {
            "g_tk": self.g_tk,
            "qzonetoken": self.qzonetoken,
        }

        data = {
            "qzreferrer": "https://qzs.qq.com/qzone/msgboard/msgbcanvas.html",
            "content": content,
            "hostUin": uin,
            "uin": self.uin,
            "format": "fs",
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "iNotice": 1,
            "ref": "qzone",
            "json": 1,
            "g_tk": self.g_tk,
        }

        rep = self.session.post(url, headers=Agent, params=params, data=data)
        return rep

    def auto_comment(self, uin, mood_id, content):
        """
        指定好友说说自动评论
        :param int | uin: 好友账号
        :param str | mood_id: 说说编号
        :param str | content: 评论内容
        :return: 评论结果信息Response对象
        """
        url = "https://h5.qzone.qq.com/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_addcomment_ugc"
        params = {
            "g_tk": self.g_tk,
            "qzonetoken": self.qzonetoken,
        }
        data = {
            "qzreferrer": "qzreferrer:https://qzs.qq.com/qzone/app/mood_v6/html/index.html",
            "uin": 584350987,
            "hostUin": uin,
            "topicId": str(uin) + "_" + mood_id,
            "commentUin": self.uin,
            "content": content,
            "richval": "",
            "richtype": "",
            "inCharset": "",
            "outCharset": "",
            "ref": "",
            "private": "",
            "with_fwd": 0,
            "to_tweet": 0,
            "hostuin": uin, # ?
            "code_version": 1,
            "format": "fs",
        }
        rep = self.session.post(url, headers=Agent, params=params, data=data)
        return rep

    def auto_reply_comment(self, uin, mood_id, comment_id, comment_uin, content):
        """
        自动回复指定好友指定说说。
        :param int | uin: 好友账号
        :param str | mood_id: 说说编号
        :param str | comment_id: 评论编号
        :param str | comment_uin: 评论者
        :param str content: 回复内容
        :return: 回复结果Response对象
        """
        url = "https://h5.qzone.qq.com/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_addreply_ugc"
        params = {
            "qzreferrer": "https://qzs.qq.com/qzone/app/mood_v6/html/index.html",
            "uin": self.uin,
            "hostUin": uin,
            "topicId": str(uin) + "_" + mood_id,
            "commentId": comment_id,
            "commentUin": comment_uin,
            "content": content,
            "inCharset": "",
            "outCharset": "",
            "ref": "",
            "private": 0,
            "with_fwd": 0,
            "to_tweet": 0,
            "hostuin": uin,
            "code_version": 1,
            "format": "fs",
        }
        data = {
            "g_tk": self.g_tk,
            "qzonetoken": self.qzonetoken,
        }
        rep = self.session.post(url, headers= Agent, params=params, data=data)
        return rep

    def auto_delete_comment(self, uin, mood_id, comment_id, reply_id, comment_uin, reply_uin):
        """
        自动删除评论。（这个没测试）
        :param int | uin: 好友账号
        :param str | mood_id: 说说编号
        :param int | comment_id: 评论编号
        :param int | reply_id: 回复编号
        :param int | comment_uin: 评论者账号
        :param int | reply_uin: 回复者账号
        :return: 删除结果信息对象。
        """
        url = "https://h5.qzone.qq.com/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_delreply_ugc"
        params = {
            "qzreferrer": "https://qzs.qq.com/qzone/app/mood_v6/html/index.html",
            "uin": self.uin,
            "hostUin": uin,
            "topicId": str(uin) + "_" + mood_id,
            "commentId": comment_id,
            "replyId": reply_id,
            "commentUin": comment_uin,
            "replyUin": reply_uin,
            "inCharset": "",
            "outCharset": "",
            "ref": "",
            "hostuin": uin, # ?
            "code_version": 1,
            "format": "fs",
        }
        data = {
            "g_tk": self.g_tk,
            "qzonetoken": self.qzonetoken,
        }
        rep = self.session.post(url, headers=Agent, params=params, data=data)
        return rep
