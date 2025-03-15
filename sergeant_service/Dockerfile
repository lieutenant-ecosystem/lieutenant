# Limited to Python 3.12 to prevent installing Rust for the tokenizer package (check if the same is done for 3.13 https://github.com/huggingface/tokenizers/pull/1438)
FROM python:3.12
ENV PYTHONPATH="${PYTHONPATH}:/app"

COPY .. /app
WORKDIR /app

RUN pip install -r requirements.txt --upgrade
RUN if [ "$ENVIRONMENT" != "Production" ]; then pip install -r requirements-dev.txt --upgrade; fi

WORKDIR /app/src
ENTRYPOINT ["python", "main.py"]