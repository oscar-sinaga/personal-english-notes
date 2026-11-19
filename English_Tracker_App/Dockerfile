FROM node:24-bookworm-slim@sha256:dc26ae92c9fb15cf6b1d63e20f0944b2efe0f115b20e00be48fb23fceb061c54 AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/index.html frontend/vite.config.js frontend/svelte.config.js ./
COPY frontend/src/ ./src/
COPY frontend/public/ ./public/
RUN npm run build -- --base=/workspaces/english-notes/

FROM python:3.13-slim-bookworm@sha256:a5a7017efc5969e00ae2b91c8eb0631049a569652aa4ffc4501769049ae45c72
ARG VCS_REF=unknown
LABEL org.opencontainers.image.revision=$VCS_REF
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 TZ=Asia/Jakarta TRACKER_ONLINE_HELPERS=0
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir /state /library && chown 10001:10001 /state
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/*.py backend/toc.json ./
COPY --from=frontend /build/dist /app/public/
ENV TRACKER_STATE_DIR=/state \
    TRACKER_BOOK_PATH=/library/anderson.pdf \
    TRACKER_SCORECARD_PATH=/library/siddiqi.pdf \
    TRACKER_INDEX_PATH=/library/siddiqi-index.json
USER 10001:10001
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
