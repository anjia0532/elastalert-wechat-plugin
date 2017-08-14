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

    #echo -e "http://mirrors.ustc.edu.cn/alpine/v3.4/main\nhttp://mirrors.ustc.edu.cn/alpine/v3.4/community" > /etc/apk/repositories && \
    
    apk update && apk upgrade && apk add bash curl tar musl-dev linux-headers g++ libffi-dev libffi openssl-dev && \
    
    mkdir -p ${ELASTALERT_PLUGIN_DIRECTORY} && \
    mkdir -p ${RULES_DIRECTORY} && \
    
    curl -Lo elastalert.tar.gz ${ELASTALERT_URL} && \
    tar -xzvf elastalert.tar.gz -C ${ELASTALERT_HOME} --strip-components 1 && \
    rm elastalert.tar.gz && \
    
    pip install "requests==2.18.1" && \
    pip install "setuptools>=11.3" && \
    python setup.py install

COPY ./start-elastalert.sh /opt/start-elastalert.sh
RUN chmod +x /opt/start-elastalert.sh

COPY ./config.yaml /opt/elastalert/
COPY ./rules/* ${RULES_DIRECTORY}/
COPY ./elastalert_modules/* ${ELASTALERT_PLUGIN_DIRECTORY}/

# Launch Elastalert when a container is started.
CMD ["/opt/start-elastalert.sh"]
