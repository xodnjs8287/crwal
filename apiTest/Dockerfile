# 1. 베이스 이미지 선택: Python 3.10 버전을 기반으로 시작합니다.
FROM python:3.10-slim

# 2. 시스템 업데이트 및 크롬 브라우저 설치에 필요한 도구 설치
# RUN: Docker 이미지를 만드는 과정에서 실행되는 명령어입니다.
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    --no-install-recommends

# 3. 구글 크롬 브라우저 공식 버전 설치
# 서버 환경에 실제 크롬 브라우저를 설치하는 과정입니다.
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable --no-install-recommends

# 4. 프로젝트 코드를 복사할 작업 디렉토리 생성
WORKDIR /app

# 5. requirements.txt 파일을 먼저 복사하고, 라이브러리 설치
# 이렇게 하면, 파이썬 코드만 바뀔 경우 라이브러리를 다시 설치하지 않아 속도가 빨라집니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. 나머지 모든 프로젝트 파일(app.py 등)을 복사
COPY . .

# 7. 서버가 시작될 때 실행할 명령어 설정
# Gunicorn을 사용하여 8080 포트에서 앱을 실행합니다.
# --timeout 0: 크롤링 작업이 길어져도 연결이 끊기지 않게 하는 매우 중요한 옵션입니다.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "0", "app:app"]
