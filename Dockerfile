FROM python:3.10.8-alpine as builder

ARG PIP_PYMILTER_VERSION=1.0.5
WORKDIR /build

RUN apk update
RUN apk add libmilter libmilter-dev python3 python3-dev py3-pip gcc libgcc libc-dev make

RUN pip install -t "/build/pymilter" "pymilter==${PIP_PYMILTER_VERSION}"
ENV PYTHONPATH=/build/pymilter:${PYTHONPATH}

COPY . /build

RUN make build

RUN ls -la 
RUN ls -la dist

FROM python:3.10.8-alpine

ARG APP_VERSION=dev
ARG POSTFIX_MILTER_LOGLEVEL="INFO"

ENV PYTHONPATH=/pymilter:${PYTHONPATH}

LABEL org.opencontainers.image.title="milter-framework"
LABEL org.opencontainers.image.description="Postfix Milter daemon with pluggable modules."
LABEL org.opencontainers.image.authors="Pavel Kim <hello@pavelkim.com>"
LABEL org.opencontainers.image.url="https://github.com/milter-framework/milter-framework"
LABEL org.opencontainers.image.version="${APP_VERSION}"

RUN mkdir -pv /app/output /app/logs
WORKDIR /app

RUN apk update && \
  apk add libmilter

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY --from=builder /build/pymilter /pymilter
COPY --from=builder "/build/dist/milter_framework-${APP_VERSION}-py2.py3-none-any.whl" "/app/milter_framework-${APP_VERSION}-py2.py3-none-any.whl"
# COPY "docker/lib/pmm_output_file-1.0.0-py2.py3-none-any.whl" "/app/pmm_output_file-1.0.0-py2.py3-none-any.whl"
RUN pip install "/app/milter_framework-${APP_VERSION}-py2.py3-none-any.whl"
# RUN pip install "/app/pmm_output_file-1.0.0-py2.py3-none-any.whl"

ENTRYPOINT ["pmm"]
