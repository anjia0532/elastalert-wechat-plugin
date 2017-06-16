#! /usr/bin/env python 
# -*- coding: utf-8 -*-

#from __future__ import unicode_literals 
import urllib,urllib2
import json
import sys
import datetime
from elastalert.alerts import Alerter, BasicMatchString
from requests.exceptions import RequestException
from elastalert.util import elastalert_logger
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
        #self.expires_in=datetime.datetime.now() - datetime.timedelta(seconds=60)

    def create_default_title(self, matches):
        subject = 'ElastAlert: %s' % (self.rule['name'])
        return subject

    def alert(self, matches):
        
        if not self.party_id and not self.user_id and not self.tag_id:
            elastalert_logger.warn("All touser & toparty & totag invalid")
        
        # 参考elastalert的写法
        # https://github.com/Yelp/elastalert/blob/master/elastalert/alerts.py#L236-L243
        body = self.create_alert_body(matches)

        # 微信企业号获取Token文档
        # http://qydev.weixin.qq.com/wiki/index.php?title=AccessToken
        self.get_token()
        
        self.senddata(body)
        
        elastalert_logger.info("send message to %s" % (self.corp_id))

    def get_token(self):

        #获取token是有次数限制的,本想本地缓存过期时间和token，但是elastalert每次调用都是一次性的，不能全局缓存
        #if self.expires_in >= datetime.datetime.now() and not self.access_token:
        #    return self.access_token

        #构建获取token的url
        get_token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=' + self.corp_id + '&corpsecret=' + self.secret

        try:
            token_file = urllib2.urlopen(get_token_url)
        except urllib2.HTTPError as e:
            raise EAException("get access_token failed , http code : %s, http response content:%s" % e.code,e.read().decode("utf8"))
            sys.exit()

        token_data = token_file.read().decode('utf-8')
        token_json = json.loads(token_data)
        token_json.keys()
        
        if token_json['access_token'] is None :
            elastalert_logger.warn("get access_token failed , the response is : %s" % token_data)
            sys.exit()
        
        #获取access_token和expires_in
        self.access_token = token_json['access_token']
        #self.expires_in = datetime.datetime.now() + datetime.timedelta(seconds=token_json['expires_in'])
        
        return self.access_token

    def senddata(self, content):
        
        # 微信企业号有字符长度限制，超长自动截断

        if len(content) > 2000:
            content = content[:1997] + "..."

        # 微信发送消息文档
        # http://qydev.weixin.qq.com/wiki/index.php?title=%E6%B6%88%E6%81%AF%E7%B1%BB%E5%9E%8B%E5%8F%8A%E6%95%B0%E6%8D%AE%E6%A0%BC%E5%BC%8F
        send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + self.access_token

        headers = {'content-type': 'application/json'}

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
