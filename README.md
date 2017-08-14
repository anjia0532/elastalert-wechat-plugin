# elastalert-wechat-plugin

基于ElastAlert的微信企业号报警插件

## 使用说明
使用说明详见 https://anjia.ml/2017/02/16/elastalert-wechat-plugin/

## 常见问题
1. 如果遇到运行一段时间后，报警规则莫名被禁用，则 详见 https://github.com/anjia0532/elastalert-wechat-plugin/issues/2

1. 如果报 `SSLError(SSLError("bad handshake: Error([('SSL routines', SSL3_GET_SERVER_CERTIFICATE', 'certificate verify failed')],)",),)` 参见 [简书#SSLError](http://www.jianshu.com/p/cb8adfca598a)，如果对于安全要求不高的话，可以 修改 [wechat_qiye_alert.py#L73](https://github.com/anjia0532/elastalert-wechat-plugin/blob/master/wechat_qiye_alert.py#L73) 和 [wechat_qiye_alert.py#L126](https://github.com/anjia0532/elastalert-wechat-plugin/blob/master/wechat_qiye_alert.py#L126)加入 `verify=False` 但是 此为不校验证书，容易导致中间人攻击等问题。具体解决方案自行搜索google `python2.7 SNI`

## 使用Docker
ubuntu 16.04 python 2.7.12 正常，如果条件允许，建议使用docker镜像，减少环境差异导致的各种奇葩问题

docker hub repo [anjia0532/elastalert-wechat-plugin](https://hub.docker.com/r/anjia0532/elastalert-wechat-plugin/)

```bash

#默认docker官方库
docker pull anjia0532/elastalert-wechat-plugin

#阿里云镜像库
docker pull registry.cn-hangzhou.aliyuncs.com/shunneng/elastalert-wechat-plugin
```

### 环境变量说明

`ELASTICSEARCH_HOST`: elasticsearch host

`ELASTICSEARCH_PORT`: elasticsearch port

`ELASTICSEARCH_USERNAME`: elasticsearch用户名

`ELASTICSEARCH_PASSWORD`: elasticsearch密码

`SET_CONTAINER_TIMEZONE`: 是否要设置时区，true|false 

`CONTAINER_TIMEZONE`: 时区，默认北京时间东八区 `Asia/Shanghai`

