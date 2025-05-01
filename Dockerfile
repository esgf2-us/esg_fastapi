FROM python:3.12

ARG PIP_EXTRA_INDEX_URL
ARG ESG_FASTAPI_VERSION

WORKDIR /app

RUN export PIP_EXTRA_INDEX_URL="$PIP_EXTRA_INDEX_URL" && \
    export ESGFHUB_VERSION="$ESG_FASTAPI_VERSION" && \
    pip install \
    esg_fastapi==$ESG_FASTAPI_VERSION \
    --no-cache-dir \
    --report -

ENV PROMETHEUS_MULTIPROC_DIR /dev/shm

CMD ["uvicorn", "esg_fastapi.wsgi:app", "--host", "0.0.0.0", "--port", "1337"]
