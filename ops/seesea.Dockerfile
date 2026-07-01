FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir seesea==2.2.2 "click>=8.3.1"

EXPOSE 18080

CMD ["seesea", "server", "--host", "0.0.0.0", "--port", "18080"]
