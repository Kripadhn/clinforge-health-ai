FROM python:3.11-slim
WORKDIR /srv
RUN pip install --no-cache-dir "mcp>=1.2,<2" httpx
COPY shared/clinical_shared ./clinical_shared
COPY mcp-server/mcp_clinical_server ./mcp_clinical_server
EXPOSE 8002
CMD ["python", "-m", "mcp_clinical_server.server"]
