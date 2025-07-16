FROM python:3.11-slim

# 安裝 Chrome 和相關依賴
RUN apt-get update && \
    apt-get install -y wget gnupg2 curl unzip fonts-liberation libnss3 libgconf-2-4 libxi6 libxcursor1 libxdamage1 libxtst6 libxrandr2 xdg-utils --no-install-recommends && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
WORKDIR /app

# 重要：讓 Uvicorn 跑在外部可訪問的 port
CMD ["uvicorn", "UOF_coc_get:app", "--host", "0.0.0.0", "--port", "10000"]
