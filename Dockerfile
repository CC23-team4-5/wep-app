FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY static ./static
COPY templates ./templates
COPY data ./data
COPY app.py .

EXPOSE 8080

CMD ["python", "app.py"]