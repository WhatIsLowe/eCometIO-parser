FROM python:3.12

WORKDIR /api

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY wait-for-it.sh ./
RUN chmod +x ./wait-for-it.sh

COPY . .

CMD ["./wait-for-it.sh", "postgres:5432", "--", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]