FROM python:3.11-slim

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

COPY main.py .

RUN mkdir -p /var/log/app && chown -R appuser:appgroup /var/log/app

USER appuser

ENV MODE=stable
ENV APP_VERSION=1.0.0
ENV APP_PORT=3000

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:3000/healthz')" || exit 1

CMD ["python3", "main.py"]
