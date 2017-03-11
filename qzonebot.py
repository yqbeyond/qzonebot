import threading
import queue

from .core import Client
import requests
import json


# 可以参考图灵机器人官网设置apikey和userId
tuling_api = "http://www.tuling123.com/openapi/api"
apikey = ""
userId = ""


def ask_tuling_bot(msg):
    """
    :param str | msg: 给图灵机器人发的消息
    :return: 图灵机器人的回复，失败返回 None
    """
    data = {
        "key": apikey,
        "info": msg,
        "userId": userId,
    }
    rep = requests.post(tuling_api, data=data)
    res = json.loads(rep.text)
    if res("code") == 100000:
        return res
    else:
        return None


def auto_comment_all(self, uin):
    """
    一个自动评论指定好友所有说说的例子
    :param int | uin: 好友账号
    """
    coll = self.db.moods
    moods = coll.find({"uin": uin})  # 从数据库找到指定好友的所有说说
    tid_content_list = [{"tid": mood["tid"], "content": mood["content"]} for mood in moods]  # 只关心说说id和内容
    for item in tid_content_list:
        reply = ask_tuling_bot(item['content'])  # 将好友的消息发给图灵机器人看看图灵机器人怎么说
        self.auto_comment(uin=uin, mood_id=item['tid'], content=reply)

if __name__ == "__main__":
    client = Client()
    client.login()

    uin = 123456789  # 好友QQ
    # client.crawl_mood(uin)  # 如果第一次使用， 先调用此函数抓取指定好友的所有说说。（可能会漏爬）
    auto_comment_all(client)


