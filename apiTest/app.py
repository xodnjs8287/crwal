from flask import Flask, request, jsonify
import time
import uuid
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# webdriver-manager는 Docker 환경에서 필요 없습니다.

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
        
        # === ★★★ 메모리 최적화를 위한 옵션 추가 ★★★ ===
        # 이미지를 불러오지 않도록 설정하여 메모리 사용량을 대폭 줄입니다.
        options.add_argument("--disable-images")
        options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
        # ===============================================

        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(service=Service(), options=options)
        # 페이지 로드 타임아웃을 30초로 설정합니다. 페이지가 30초 안에 로드되지 않으면 오류를 발생시킵니다.
        driver.set_page_load_timeout(30)
        
        driver.get(URL)
        time.sleep(2)
#dd
        # '더보기' 버튼 클릭
        for i in range(click_count):
            try:
                driver.find_element(By.CSS_SELECTOR, 'a.api_more').click()
                time.sleep(1)
            except NoSuchElementException:
                break
        
        posts = driver.find_elements(By.CSS_SELECTOR, "li.bx")
        links_to_visit = []
        for post in posts:
            try:
                link = post.find_element(By.CSS_SELECTOR, 'a.title_link').get_attribute('href')
                links_to_visit.append(link)
            except NoSuchElementException:
                continue

        print(f"[작업 ID: {task_id}] 총 {len(links_to_visit)}개의 블로그 링크 수집 완료. 본문 확인을 시작합니다.")

        results = []
        for link in links_to_visit:
            try:
                driver.get(link)
                # time.sleep(2) # 페이지 로드 타임아웃을 설정했으므로, 고정 대기는 줄여도 됩니다.

                try:
                    driver.switch_to.frame('mainFrame')
                except: pass
                
                body_content = driver.find_element(By.CSS_SELECTOR, 'body').text
                
                driver.switch_to.default_content()
                title = driver.title 
                
                is_ad = any(word in body_content for word in FORBIDDEN_WORDS)
                
                if not is_ad:
                    results.append({'title': title, 'link': link})
                    print(f"✅ 맛집 게시물 추가: {title}")
                else:
                    print(f"🚫 광고 게시물 건너뛰기: {title}")

            except Exception as e:
                print(f"'{link}' 처리 중 오류 발생: {e}")
                continue
                
        driver.quit()
        
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['results'] = results
        print(f"\n[작업 ID: {task_id}] 크롤링 성공! 총 {len(results)}개의 맛집 정보를 찾았습니다.")

    except Exception as e:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)
        print(f"\n[작업 ID: {task_id}] 크롤링 실패: {e}")


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
