FROM python:3.12
ENV PYTHONPATH="${PYTHONPATH}:/app"

COPY .. /app
WORKDIR /app

RUN pip install -r requirements.txt --upgrade
RUN if [ "$ENVIRONMENT" != "Production" ]; then pip install -r requirements-dev.txt --upgrade; fi

WORKDIR /app/src
ENTRYPOINT ["python", "main.py"]