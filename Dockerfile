FROM cainelli/k8s-tools

RUN apk add --update \
    python \
    python-dev \
    py-pip \
    build-base \
    && pip install awscli --upgrade --user \
    && apk --purge -v del py-pip \
    && rm -rf /var/cache/apk/*

ADD ci-kustomize.py /

ENTRYPOINT [ "/ci-kustomize.py" ]
