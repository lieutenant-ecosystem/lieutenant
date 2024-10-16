FROM python:latest

COPY .. /app
WORKDIR /app

RUN pip install -r requirements.txt
RUN if [ "$ENVIRONMENT" != "Production" ]; then pip install -r requirements-dev.txt; fi
ENTRYPOINT ["python", "main.py"]