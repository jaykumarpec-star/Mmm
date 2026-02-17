FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ⭐ VERY IMPORTANT LINE
RUN playwright install --with-deps chromium

COPY . .

CMD ["python", "bot.py"]
