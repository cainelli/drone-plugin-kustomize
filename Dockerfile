FROM cainelli/k8s-tools

COPY ci-kustomize.py /
COPY requirements.txt /

WORKDIR /

RUN apk add --update \
    python3 \
    && pip3 install -r requirements.txt 

CMD /ci-kustomize.py
