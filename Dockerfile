FROM python:3

ARG PIP_EXTRA_INDEX_URL
ARG ESG_FASTAPI_VERSION

WORKDIR /app

RUN export PIP_EXTRA_INDEX_URL="$PIP_EXTRA_INDEX_URL" && \
    export ESGFHUB_VERSION="$ESG_FASTAPI_VERSION" && \
    pip install \
    esg_fastapi==$ESG_FASTAPI_VERSION \
    --no-cache-dir \
    --report -

ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8080
CMD ["uvicorn", "esg_fastapi:api"]