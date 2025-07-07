# 1. 베이스 이미지 설정 (가벼운 slim 버전 사용)
FROM python:3.11-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 필요한 라이브러리 목록 파일 복사
COPY requirements.txt .

# 4. 라이브러리 설치 (캐시를 사용하지 않아 이미지 용량을 줄임)
RUN pip install --no-cache-dir -r requirements.txt

# 5. 프로젝트의 모든 파일(.py 등)을 작업 디렉토리로 복사
COPY . .

# 6. 컨테이너가 시작될 때 실행할 명령어
# app.py는 실제 실행할 파이썬 파일명으로 수정하세요.
CMD ["python", "app.py"]