#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
import datetime
from elastalert.alerts import Alerter, BasicMatchString
from requests.exceptions import RequestException
from elastalert.util import elastalert_logger,EAException #[感谢minminmsn分享](https://github.com/anjia0532/elastalert-wechat-plugin/issues/2#issuecomment-311014492)
import requests

'''
#################################################################
# 微信企业号推送消息                                              #
#                                                               #
# 作者: AnJia <anjia0532@gmail.com>                              #
# 作者博客: https://anjia.ml/                                    #
# Github: https://github.com/anjia0532/elastalert-wechat-plugin #
#                                                               #
#################################################################
'''
class WeChatAlerter(Alerter):

    #企业号id，secret，应用id必填

    required_options = frozenset(['corp_id','secret','agent_id'])

    def __init__(self, *args):
        super(WeChatAlerter, self).__init__(*args)
        self.corp_id = self.rule.get('corp_id', '')     #企业号id
        self.secret = self.rule.get('secret', '')       #secret
        self.agent_id = self.rule.get('agent_id', '')   #应用id

        self.party_id = self.rule.get('party_id')       #部门id
        self.user_id = self.rule.get('user_id', '')     #用户id，多人用 | 分割，全部用 @all
        self.tag_id = self.rule.get('tag_id', '')       #标签id
        self.access_token = ''                          #微信身份令牌
        self.expires_in=datetime.datetime.now() - datetime.timedelta(seconds=60)

    def create_default_title(self, matches):
        subject = 'ElastAlert: %s' % (self.rule['name'])
        return subject

    def alert(self, matches):

        if not self.party_id and not self.user_id and not self.tag_id:
            elastalert_logger.warn("All touser & toparty & totag invalid")

        # 参考elastalert的写法
        # https://github.com/Yelp/elastalert/blob/master/elastalert/alerts.py#L236-L243
        body = self.create_alert_body(matches)

        #matches 是json格式
        #self.create_alert_body(matches)是String格式,详见 [create_alert_body 函数](https://github.com/Yelp/elastalert/blob/master/elastalert/alerts.py)

        # 微信企业号获取Token文档
        # http://qydev.weixin.qq.com/wiki/index.php?title=AccessToken
        self.get_token()

        self.senddata(body)

        elastalert_logger.info("send message to %s" % (self.corp_id))

    def get_token(self):

        #获取token是有次数限制的,本想本地缓存过期时间和token，但是elastalert每次调用都是一次性的，不能全局缓存
        if self.expires_in >= datetime.datetime.now() and self.access_token:
            return self.access_token

        #构建获取token的url
        get_token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s' %(self.corp_id,self.secret)

        try:
            response = requests.get(get_token_url)
            response.raise_for_status()
        except RequestException as e:
            raise EAException("get access_token failed , stacktrace:%s" % e)
            #sys.exit("get access_token failed, system exit")

        token_json = response.json()

        if 'access_token' not in token_json :
            raise EAException("get access_token failed , , the response is :%s" % response.text())
            #sys.exit("get access_token failed, system exit")

        #获取access_token和expires_in
        self.access_token = token_json['access_token']
        self.expires_in = datetime.datetime.now() + datetime.timedelta(seconds=token_json['expires_in'])

        return self.access_token

    def senddata(self, content):

        #如果需要原始json，需要传入matches

        # http://qydev.weixin.qq.com/wiki/index.php?title=%E6%B6%88%E6%81%AF%E7%B1%BB%E5%9E%8B%E5%8F%8A%E6%95%B0%E6%8D%AE%E6%A0%BC%E5%BC%8F
        # 微信企业号有字符长度限制（2048），超长自动截断

        # 参考 http://blog.csdn.net/handsomekang/article/details/9397025
        #len utf8 3字节，gbk2 字节，ascii 1字节
        if len(content) > 2048:
            content = content[:2045] + "..."

        # 微信发送消息文档
        # http://qydev.weixin.qq.com/wiki/index.php?title=%E6%B6%88%E6%81%AF%E7%B1%BB%E5%9E%8B%E5%8F%8A%E6%95%B0%E6%8D%AE%E6%A0%BC%E5%BC%8F
        send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s' %( self.access_token)

        headers = {'content-type': 'application/json'}

        #最新微信企业号调整校验规则，tagid必须是string类型，如果是数字类型会报错，故而使用str()函数进行转换
        payload = {
            "touser": self.user_id and str(self.user_id) or '', #用户账户，建议使用tag
            "toparty": self.party_id and str(self.party_id) or '', #部门id，建议使用tag
            "totag": self.tag_id and str(self.tag_id) or '', #tag可以很灵活的控制发送群体细粒度。比较理想的推送应该是，在heartbeat或者其他elastic工具自定义字段，添加标签id。这边根据自定义的标签id，进行推送
            'msgtype': "text",
            "agentid": self.agent_id,
            "text":{
                "content": content.encode('UTF-8') #避免中文字符发送失败
               },
            "safe":"0"
        }

        # set https proxy, if it was provided
        # 如果需要设置代理，可修改此参数并传入requests
        # proxies = {'https': self.pagerduty_proxy} if self.pagerduty_proxy else None
        try:
            response = requests.post(send_url, data=json.dumps(payload, ensure_ascii=False), headers=headers)
            response.raise_for_status()
        except RequestException as e:
            raise EAException("send message has error: %s" % e)

        elastalert_logger.info("send msg and response: %s" % response.text)


    def get_info(self):
        return {'type': 'WeChatAlerter'}
