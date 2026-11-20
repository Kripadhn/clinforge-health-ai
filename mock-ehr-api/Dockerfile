FROM python:3.11-slim
WORKDIR /srv
RUN pip install --no-cache-dir fastapi "uvicorn[standard]"
COPY mock-ehr-api/app ./app
ENV CLINFORGE_DB=/data/clinical.db
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
