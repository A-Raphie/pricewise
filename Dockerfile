# ---- Stage 1: build the dashboard (static) ----
FROM node:20-slim AS web
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml tsconfig.base.json .npmrc ./
COPY packages ./packages
COPY apps/web ./apps/web
RUN pnpm install --frozen-lockfile
RUN pnpm --filter @pricewise/sdk build && pnpm --filter @pricewise/web build

# ---- Stage 2: Python engine, serving the built dashboard at / ----
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir fastapi 'uvicorn[standard]' httpx openai langgraph
COPY valuation-engine/pricewise_engine ./pricewise_engine
COPY --from=web /app/apps/web/dist ./static
ENV STATIC_DIR=/app/static
EXPOSE 8000
CMD ["uvicorn", "pricewise_engine.app:app", "--host", "0.0.0.0", "--port", "8000"]
