FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# MOST IMPORTANT LINE
RUN python -m playwright install --with-deps chromium

CMD ["python", "bot.py"]
