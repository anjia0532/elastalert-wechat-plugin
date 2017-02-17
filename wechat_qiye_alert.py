#! /usr/bin/env python 
# -*- coding: utf-8 -*-

import urllib,urllib2
import json
import sys
import datetime
from elastalert.alerts import Alerter, BasicMatchString
from requests.exceptions import RequestException
from elastalert.util import elastalert_logger
import requests

'''
##########################################################
# 微信企业号推送消息                                       #
#                                                        #
# 作者: AnJia <anjia0532@gmail.com>                       #
# 作者博客: https://anjia.ml/                             #
# Github: https://github.com/anjia0532/weixin-qiye-alert #
#                                                        #
##########################################################
'''
class WeChatAlerter(Alerter):

	#企业号id，secret，应用id必填
    required_options = frozenset(['corp_id','secret','agent_id'])

    def __init__(self, *args):
        super(WeChatAlerter, self).__init__(*args)
        self.corp_id = self.rule.get('corp_id', '') 	#企业号id
        self.secret = self.rule.get('secret', '') 		#secret
        self.agent_id = self.rule.get('agent_id', '')	#应用id

        self.party_id = self.rule.get('party_id') 		#部门id
        self.user_d = self.rule.get('user_d', '') 		#用户id，多人用 | 分割，全部用 @all
        self.tag_id = self.rule.get('tag_id', '') 		#标签id
        self.access_token = ''                          #微信身份令牌
        #self.expires_in=datetime.datetime.now() - datetime.timedelta(seconds=60)
        
        self.headers = {'content-type': 'application/json'}

    def create_default_title(self, matches):
        subject = 'ElastAlert: %s' % (self.rule['name'])
        return subject

    def alert(self, matches):
    	
        # https://github.com/Yelp/elastalert/blob/master/elastalert/alerts.py#L236-L243
        body = self.create_alert_body(matches)

        # 获取微信企业号的accessToken
        # http://qydev.weixin.qq.com/wiki/index.php?title=AccessToken
        self.get_token()
        
        self.send_data(body)
        
        elastalert_logger.info("发送消息给 %s" % (self.corp_id))

    def get_token(self):

    	#构建获取token的url
        get_token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=' + self.corp_id + '&corpsecret=' + self.secret

        try:
            response = requests.get(get_token_url, headers=self.headers)
            response.raise_for_status()
        except RequestException as e:
            raise EAException("推送微信消息--获取accessToken时失败: %s" % e)
            sys.exit()

        token_json = json.loads(response.text)
        token_json.keys()

        #获取access_token和expires_in
        self.access_token = token_json['access_token']
        #self.expires_in = datetime.datetime.now() + datetime.timedelta(seconds=token_json['expires_in'])
        
        return self.access_token

    
    def send_data(self, content):
        
        # 微信企业号文本消息有字符长度限制,文档上说限制1000字符,但是我实际测试,可以上传2090个字符
        # 超长的进行截断处理
        if len(content) > 2000:
            content = content[:1997] + "..."
        
        send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + self.access_token

        payload = {
            'totag': self.tag_id,
            'msgtype': "text",
            "agentid": self.agent_id,
            "text":{
                "content": content.encode('UTF-8')
               },
            "safe":"0"
        }


        print len(content)
        
        # set https proxy, if it was provided
        # proxies = {'https': self.pagerduty_proxy} if self.pagerduty_proxy else None
        try:
            response = requests.post(send_url, data=json.dumps(payload, ensure_ascii=False), headers=headers)
            response.raise_for_status()
        except RequestException as e:
            raise EAException("推送微信消息失败: %s" % e)
        elastalert_logger.info("推送微信报警")

        print response.text
       

    def get_info(self):
        return {'type': 'WeChatAlerter'}