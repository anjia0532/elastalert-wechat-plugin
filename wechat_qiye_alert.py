# encoding: utf-8
import urllib,urllib2
import json
import sys
import datetime
from elastalert.alerts import Alerter, BasicMatchString

from elastalert.util import elastalert_logger

'''
##########################################################
# 微信企业号推送消息                                     #
#                                                        #
# 作者: AnJia <anjia0532@gmail.com>                      #
# 作者博客: https://anjia.ml/                            #
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

    def create_default_title(self, matches):
        subject = 'ElastAlert: %s' % (self.rule['name'])
        return subject

    def alert(self, matches):
    	# https://github.com/Yelp/elastalert/blob/master/elastalert/alerts.py#L236-L243
        body = self.create_alert_body(matches)

        # http://qydev.weixin.qq.com/wiki/index.php?title=AccessToken
        self.get_token()
        
        print self.access_token
        #print self.expires_in

        self.senddata(body)
        elastalert_logger.info("发送消息给 %s" % (self.corp_id))

    def get_token(self):

        #if self.expires_in >= datetime.datetime.now() and not self.access_token:
        #    return self.access_token

    	#构建获取token的url
        get_token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=' + self.corp_id + '&corpsecret=' + self.secret

        try:
            token_file = urllib2.urlopen(get_token_url)
        except urllib2.HTTPError as e:
            print e.code
            print e.read().decode("utf8")
            sys.exit()

        token_data = token_file.read().decode('utf-8')
        token_json = json.loads(token_data)
        token_json.keys()

        #获取access_token和expires_in
        self.access_token = token_json['access_token']
        #self.expires_in = datetime.datetime.now() + datetime.timedelta(seconds=token_json['expires_in'])
        
        return self.access_token

    def senddata(self, content):
        send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + self.access_token
        send_values = {
            "totag":self.tag_id,
            "touser":self.user_d,
            "toparty": self.party_id,
            "msgtype":"text",
            "agentid":self.agent_id,
            "text":{
                "content":content
               },
            "safe":"0"
            }

        send_data = json.dumps(send_values, ensure_ascii=False)

        send_request = urllib2.Request(send_url, send_data)

        response = json.loads(urllib2.urlopen(send_request).read())

        print str(response)

    def get_info(self):
        return {'type': 'WeChatAlerter'}