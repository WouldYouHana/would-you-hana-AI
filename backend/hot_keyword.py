from apscheduler.schedulers.background import BackgroundScheduler
import json
import logging
import pytz
import pymysql
from konlpy.tag import Komoran
from collections import Counter

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# DB 연결 설정
db_config = {
    'host': '172.18.0.2',
    'user': 'scott',
    'password': 'tiger',
    'database': 'db'
}

# 사용자 사전 로드
def load_user_dictionary(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return set(line.strip().split('\t')[0] for line in f if line.strip())
    except Exception as e:
        print(f"사전 로드 오류: {e}")
        return set()

# DB에서 지역 데이터 가져오기
def fetch_location_from_db():
    try:
        # DB 연결
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()

        # 데이터 조회 쿼리
        query = "SELECT location FROM location;"
        cursor.execute(query)

        # 결과 가져오기
        rows = cursor.fetchall()
        return [row[0] for row in rows]

    except Exception as e:
        print(f"DB 오류: {e}")
        return []
    finally:
        if 'connection' in locals():
            connection.close()

# DB에서 데이터 가져오기
def fetch_data_from_db(location):
    try:
        # DB 연결
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()

        # 데이터 조회 쿼리
        query = "SELECT content FROM question WHERE location = %s"
        cursor.execute(query, (location,))

        # 결과 가져오기
        rows = cursor.fetchall()
        return [row[0] for row in rows]

    except Exception as e:
        print(f"DB 오류: {e}")
        return []
    finally:
        if 'connection' in locals():
            connection.close()

# 인기 키워드를 DB에 저장
def save_keywords_to_db(keywords, location):
    try:
        # DB 연결
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()

        # 테이블이 없다면 생성
        create_table_query = """
                    CREATE TABLE IF NOT EXISTS popular_keywords (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        keyword VARCHAR(255) NOT NULL,
                        location VARCHAR(255) NOT NULL
                    );
                """
        cursor.execute(create_table_query)
        connection.commit()

        # 기존 데이터 삭제
        delete_query = "DELETE FROM popular_keywords WHERE location = %s"
        cursor.execute(delete_query, (location,))

        # 키워드를 DB에 저장
        for keyword, count in keywords:
            query = "INSERT INTO popular_keywords (keyword, location) VALUES (%s, %s)"
            cursor.execute(query, (keyword, location))

        connection.commit()

    except Exception as e:
        print(f"DB 저장 오류: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

# 키워드 추출 및 사용자 사전 기반 필터링
def extract_popular_keywords(data, user_dict):
    komoran = Komoran()
    all_keywords = []

    for text in data:
        # 형태소 단위로 분석
        morphs = komoran.morphs(text)

        # 사용자 사전에 있는 키워드만 필터링
        filtered_keywords = [kw for kw in user_dict if kw in text]
        all_keywords.extend(filtered_keywords)

    # 키워드 빈도 계산
    counter = Counter(all_keywords)
    return counter.most_common(5)  # 상위 5개 인기 키워드 반환

def update_popular_keywords():
    try:
        logging.info("인기 키워드 업데이트 시작...")

        # 사용자 사전 로드
        user_dict_path = '/app/data/user_dict.txt'
        user_dict = load_user_dictionary(user_dict_path)

        if not user_dict:
            logging.error("사용자 사전을 로드하지 못했습니다.")
            return

        # DB에서 locations 데이터 가져오기
        locations = fetch_location_from_db()

        if not locations:
            logging.error("DB에서 locations 데이터를 가져올 수 없습니다.")
            return

        for location in locations:
            # DB에서 데이터 가져오기
            data = fetch_data_from_db(location)

            if not data:
                logging.warning(f"{location}에 대한 데이터를 가져올 수 없습니다.")
                continue

            # 인기 키워드 추출
            popular_keywords = extract_popular_keywords(data, user_dict)

            # DB에 인기 키워드 저장
            save_keywords_to_db(popular_keywords, location)

        logging.info("인기 키워드 업데이트 완료.")
    except Exception as e:
        logging.error(f"키워드 업데이트 중 오류 발생: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Seoul'))
    # 매일 자정에 작업 예약
    scheduler.add_job(update_popular_keywords, 'cron', hour=0, minute=0)

    scheduler.start()
    logging.info("스케줄러가 시작되었습니다.")

# 직접 실행 시 스케줄러 시작
if __name__ == "__main__":
    start_scheduler()