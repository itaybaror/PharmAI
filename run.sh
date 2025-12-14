docker run --name pharmai-container \
  -p 8080:8000 \
  -v "$(pwd)":/app \
  --env-file .env \
  pharmai