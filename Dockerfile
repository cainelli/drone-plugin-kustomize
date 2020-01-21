FROM cainelli/k8s-tools

RUN apk add --update \
    python3 \
    && pip3 install awscli --upgrade

WORKDIR /

COPY ci-kustomize.py /

ENTRYPOINT [ "/ci-kustomize.py" ]
