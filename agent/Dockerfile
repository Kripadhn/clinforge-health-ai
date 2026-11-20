FROM python:3.11-slim
WORKDIR /srv
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" "mcp>=1.2,<2" httpx pydantic
COPY shared/clinical_shared ./clinical_shared
COPY agent/agent_service ./agent_service
EXPOSE 8003
CMD ["uvicorn", "agent_service.main:app", "--host", "0.0.0.0", "--port", "8003"]
