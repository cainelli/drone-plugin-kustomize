FROM cainelli/k8s-tools

COPY ci-kustomize.py /
COPY requirements.txt /

RUN apk add --update \
    python3 \
    && pip3 install -r requirements.txt

WORKDIR /

CMD /ci-kustomize.py
