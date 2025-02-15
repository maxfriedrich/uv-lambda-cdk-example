ARG PYTHON_VERSION=3.11
ARG SOURCE_DATE_EPOCH=0

FROM public.ecr.aws/lambda/python:${PYTHON_VERSION} AS builder
ARG SOURCE_DATE_EPOCH
ENV SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}

WORKDIR /src
COPY . .
# `find` is not available in newer Lambda base images, so we use Python to walk the path and set timestamps.
RUN python -c "import os; from pathlib import Path; \
    base = Path.cwd(); \
    ts = int(os.environ['SOURCE_DATE_EPOCH']); \
    os.utime(base, (ts, ts)); \
    [os.utime(p, (ts, ts)) for p in base.rglob('*')]"

FROM public.ecr.aws/lambda/python:${PYTHON_VERSION} AS runtime
WORKDIR ${LAMBDA_TASK_ROOT}
COPY --from=builder /src .
