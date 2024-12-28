from konlpy.tag import Komoran
import pymysql
import json
from collections import Counter

# DB 연결 설정
db_config = {
    'host': '172.18.0.3',
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
