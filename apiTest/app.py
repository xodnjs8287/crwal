# 파일 이름: app.py (Docker 배포용)

from flask import Flask, request, jsonify
import time
import uuid
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# webdriver-manager는 더 이상 필요 없습니다.

# --- Flask 앱 생성 ---
app = Flask(__name__)

# --- 모든 크롤링 작업을 저장하고 상태를 추적할 변수 ---
tasks = {}


# --- 크롤링 함수 정의 (백그라운드에서 실행될 함수) ---
def naver_blog_crawler(task_id, query, click_count):
    global tasks
    try:
        tasks[task_id]['status'] = 'processing'
        print(f"[작업 ID: {task_id}] 크롤링 시작: query={query}, count={click_count}")

        URL = f"https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query={query}"
        FORBIDDEN_WORDS = ['광고', '협찬', '제공받아', '소정의', '원고료', '체험단']

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

        # Docker 환경에서는 chromedriver 경로를 자동으로 인식하므로 Service()만 사용합니다.
        # webdriver-manager가 필요 없어집니다.
        driver = webdriver.Chrome(service=Service(), options=options)

        driver.get(URL)
        time.sleep(2)

        for i in range(click_count):
            try:
                driver.find_element(By.CSS_SELECTOR, 'a.api_more').click()
                time.sleep(1)
            except NoSuchElementException:
                break

        posts = driver.find_elements(By.CSS_SELECTOR, "li.bx")
        results = []
        original_window = driver.current_window_handle

        for post in posts:
            try:
                title_tag = post.find_element(By.CSS_SELECTOR, 'a.title_link')
                title = title_tag.text
                link = title_tag.get_attribute('href')

                driver.switch_to.new_window('tab')
                driver.get(link)
                time.sleep(2)

                try:
                    driver.switch_to.frame('mainFrame')
                except:
                    pass

                body_content = driver.find_element(By.CSS_SELECTOR, 'body').text
                is_ad = any(word in body_content for word in FORBIDDEN_WORDS)

                if not is_ad:
                    results.append({'title': title, 'link': link})

                driver.close()
                driver.switch_to.window(original_window)

            except Exception as e:
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(original_window)
                continue

        driver.quit()

        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['results'] = results

    except Exception as e:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)


# --- API 엔드포인트들 (이전과 동일) ---
@app.route('/crawl', methods=['POST'])
def start_crawling_api():
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'status': 'error', 'message': 'query is required'}), 400
    query = data.get('query')
    count = data.get('count', 3)
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'pending'}
    thread = threading.Thread(target=naver_blog_crawler, args=(task_id, query, count))
    thread.start()
    return jsonify({'status': 'crawling_started', 'task_id': task_id})


@app.route('/result/<task_id>', methods=['GET'])
def get_result_api(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'status': 'error', 'message': 'task_id not found'}), 404
    return jsonify(task)


# --- 로컬 테스트용 실행 코드 (이전과 동일) ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)