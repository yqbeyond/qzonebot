from __future__ import unicode_literals


def jscallback2dict(callback_text):
    """
    将服务器返回的Callback转换成json.loads可加载的字符串
    :param callback_text:
    """
    return callback_text[callback_text.find('{'):callback_text.find(';', len(callback_text) - 2, -1) - 1]