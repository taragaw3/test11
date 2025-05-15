FROM python:3.11-slim
WORKDIR /workspace
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["functions-framework", "--target=process_video", "--port=8080"]
