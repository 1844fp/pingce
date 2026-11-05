FROM node:22-bookworm-slim AS web
WORKDIR /web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 EVAL_DB=/data/evaluation.db
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && groupadd -g 10001 evaluation && useradd -u 10001 -g evaluation -M evaluation && mkdir /data && chown evaluation:evaluation /data
COPY apps/api/ apps/api/
COPY infra/sqlite/ infra/sqlite/
COPY benchmarks/ benchmarks/
COPY integrations/ integrations/
COPY --from=web /web/dist/ apps/web/dist/
COPY infra/containers/healthcheck.py /app/healthcheck.py
USER 10001:10001
EXPOSE 8765
CMD ["python","-m","uvicorn","apps.api.main:app","--host","0.0.0.0","--port","8765"]

