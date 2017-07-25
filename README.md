# elastalert-wechat-plugin
elastalert微信企业号报警插件

基于ElastAlert的微信企业号报警插件


使用说明详见 https://anjia.ml/2017/02/16/elastalert-wechat-plugin/

如果遇到运行一段时间后，报警规则莫名被禁用，则 详见 https://github.com/anjia0532/elastalert-wechat-plugin/issues/2

如果报 `SSLError(SSLError("bad handshake: Error([('SSL routines', SSL3_GET_SERVER_CERTIFICATE', 'certificate verify failed')],)",),)` 参见 http://www.jianshu.com/p/cb8adfca598a

如果对于安全要求不高的话，可以 修改 [wechat_qiye_alert.py#L73](https://github.com/anjia0532/elastalert-wechat-plugin/blob/master/wechat_qiye_alert.py#L73) 和 [wechat_qiye_alert.py#L126](https://github.com/anjia0532/elastalert-wechat-plugin/blob/master/wechat_qiye_alert.py#L126)加入 `verify=False` 但是 此为不校验证书，容易导致中间人攻击等问题。具体解决方案自行搜索google `python2.7 SNI`

ubuntu 16.04 python 2.7.12 正常，如果条件允许，建议使用docker镜像，减少环境差异导致的各种奇葩问题

Dockerfile

```Dockerfile
FROM python:2.7-alpine

ENV SET_CONTAINER_TIMEZONE false
ENV ELASTALERT_VERSION v0.1.18
ENV CONTAINER_TIMEZONE Asia/Shanghai
ENV ELASTALERT_URL https://github.com/Yelp/elastalert/archive/${ELASTALERT_VERSION}.tar.gz
#ENV WECHAT_PLUGIN_URL https://raw.githubusercontent.com/anjia0532/elastalert-wechat-plugin/master/wechat_qiye_alert.py

ENV ELASTALERT_HOME /opt/elastalert
ENV RULES_DIRECTORY /opt/elastalert/rules
ENV ELASTALERT_PLUGIN_DIRECTORY /opt/elastalert/elastalert_modules

ENV ELASTICSEARCH_HOST http://jhipster-elasticsearch
ENV ELASTICSEARCH_PORT 9200
ENV ELASTICSEARCH_USERNAME ""
ENV ELASTICSEARCH_PASSWORD ""

WORKDIR /opt/elastalert


RUN \

    echo -e "http://mirrors.ustc.edu.cn/alpine/v3.4/main\nhttp://mirrors.ustc.edu.cn/alpine/v3.4/community" > /etc/apk/repositories && \
    
    apk update && apk upgrade && apk add bash curl tar musl-dev linux-headers g++ libffi-dev libffi openssl-dev && \
    mkdir -p ${ELASTALERT_PLUGIN_DIRECTORY} && \
    mkdir -p ${RULES_DIRECTORY} && \
    curl -Lo elastalert.tar.gz ${ELASTALERT_URL} && \
    tar -xzvf elastalert.tar.gz -C ${ELASTALERT_HOME} --strip-components 1 && \
    rm elastalert.tar.gz && \
    curl -Lo ${ELASTALERT_PLUGIN_DIRECTORY}/wechat_qiye_alert.py ${WECHAT_PLUGIN_URL} && \
    touch ${ELASTALERT_PLUGIN_DIRECTORY}/__init__.py && \
    pip install "setuptools>=11.3" && \
    python setup.py install

COPY ./start-elastalert.sh /opt/start-elastalert.sh
RUN chmod +x /opt/start-elastalert.sh

COPY ./config.yaml /opt/elastalert/
COPY ./rules/* ${RULES_DIRECTORY}/
COPY ./elastalert_modules/* ${ELASTALERT_PLUGIN_DIRECTORY}/

# Launch Elastalert when a container is started.
CMD ["/opt/start-elastalert.sh"]


```

start-elastalert.sh

```shell
#!/bin/bash
# Based on https://github.com/krizsan/elastalert-docker
echo "Waiting for Elasticsearch to startup"
while true; do
    curl ${ELASTICSEARCH_HOST}:${ELASTICSEARCH_PORT} 2>/dev/null && break
    sleep 1
done
echo "Starting Alerting"

# Set the timezone.
if [ "$SET_CONTAINER_TIMEZONE" = "true" ]; then
	unlink /etc/localtime
	ln -s /usr/share/zoneinfo/${CONTAINER_TIMEZONE} /etc/localtime && \
	echo "Container timezone set to: $CONTAINER_TIMEZONE"
else
	echo "Container timezone not modified"
fi

if [[ -n "${ELASTICSEARCH_USERNAME:-}" ]]
then
	flags="--user ${ELASTICSEARCH_USERNAME}:${ELASTICSEARCH_PASSWORD}"
else
	flags=""
fi

cd /opt/elastalert

if ! curl -f $flags ${ELASTICSEARCH_HOST}:${ELASTICSEARCH_PORT} >/dev/null 2>&1
then
	echo "Elasticsearch not available at ${ELASTICSEARCH_HOST}:${ELASTICSEARCH_PORT}"
else
	if ! curl -f $flags ${ELASTICSEARCH_HOST}:${ELASTICSEARCH_PORT}/elastalert_status >/dev/null 2>&1
	then
		echo "Creating Elastalert index in Elasticsearch..."
	    elastalert-create-index --index elastalert_status --old-index ""
	else
	    echo "Elastalert index already exists in Elasticsearch."
	fi
fi

python -m elastalert.elastalert --verbose

```
