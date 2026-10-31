FROM python:3.13.18-slim
# 호스트 스냅샷(0600일 수 있음)을 읽도록 호스트 사용자 UID로 실행한다.
ARG UID=1000
ARG GID=1000
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
 && groupadd -g "$GID" app && useradd -u "$UID" -g "$GID" -M -s /usr/sbin/nologin app \
 && mkdir -p /data/db && chown app:app /data/db
COPY app/ /app/
WORKDIR /app
USER app
EXPOSE 8787
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/health', timeout=3)"]
CMD ["python", "server.py"]
