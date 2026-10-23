FROM python:3.12-slim
WORKDIR /app
COPY python/ ./python/
COPY config/ ./config/
COPY scripts/ ./scripts/
ENV PYTHONPATH=/app/python
CMD ["python3", "-m", "itb.pipeline"]
