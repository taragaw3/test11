FROM python:3.11-slim
WORKDIR /workspace

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source
COPY . .

# Run Functions Framework on 0.0.0.0:$PORT
CMD ["functions-framework", \
     "--target=process_video", \
     "--host=0.0.0.0", \
     "--port=8080"]
