FROM python:3.9-slim

WORKDIR /app

RUN pip install elasticsearch requests python-dotenv --no-cache-dir

COPY analyzer.py .

CMD ["python3", "analyzer.py"]
