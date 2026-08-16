FROM python:3.13-slim
WORKDIR /app
COPY . .
ENTRYPOINT ["python","src/order2_observer.py"]