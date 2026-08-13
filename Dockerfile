# Pricewise single-service image: Python engine serving the prebuilt dashboard.
# The dashboard (apps/web/dist) is prebuilt and committed, so there is no Node/pnpm
# stage — keeps the cloud build fast and avoids dependency build-script issues.
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir fastapi 'uvicorn[standard]' httpx openai langgraph
COPY valuation-engine/pricewise_engine ./pricewise_engine
COPY apps/web/dist ./static
ENV STATIC_DIR=/app/static
EXPOSE 8000
CMD ["uvicorn", "pricewise_engine.app:app", "--host", "0.0.0.0", "--port", "8000"]
