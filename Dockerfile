FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Persist SQLite DB outside container
VOLUME ["/app/db"]

# Default: run the Telegram bot
CMD ["python3", "-m", "bot.main"]
