FROM --platform=linux/amd64 quay.io/modh/odh-pytorch-notebook@sha256:20f7ab8e7954106ea5e22f3ee0ba8bc7b03975e5735049a765e021aa7eb06861

run git clone -b pre-release https://github.com/NASA-IMPACT/Prithvi-WxC.git && \
    cd Prithvi-WxC/ && \
    pip install -U -e ./[examples] && \
    pip install gdown terratorch==0.99.9 s3fs && \
    # Fix permissions to support pip in OpenShift environments \
    chmod -R g+w /opt/app-root/lib/python3.11/site-packages && \
    fix-permissions /opt/app-root -P 

WORKDIR /opt/app-root/src

ENTRYPOINT ["start-notebook.sh"]