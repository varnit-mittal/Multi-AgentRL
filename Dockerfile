FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml ./
COPY whispers ./whispers
COPY openenv.yaml ./openenv.yaml
COPY README.md ./README.md

RUN pip install --no-cache-dir -e .

EXPOSE 7860
ENV WHISPERS_PORT=7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:7860/').read(); sys.exit(0)" || exit 1

CMD ["python", "-m", "whispers.server"]
