from konlpy.tag import Komoran
import pymysql
import json
from collections import Counter

# DB 연결 설정
db_config = {
    'host': 'localhost',
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

# DB에서 데이터 가져오기
def fetch_data_from_db():
    try:
        # DB 연결
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()

        # 데이터 조회 쿼리
        query = "SELECT content FROM question;"
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

# 인기 키워드를 DB에 저장
def save_keywords_to_db(keywords):
    try:
        # DB 연결
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()

        # 테이블이 없다면 생성
        create_table_query = """
        CREATE TABLE IF NOT EXISTS popular_keywords (
            id INT AUTO_INCREMENT PRIMARY KEY,
            keyword VARCHAR(255) NOT NULL,
            count INT NOT NULL
        );
        """
        cursor.execute(create_table_query)
        connection.commit()

        # 키워드를 DB에 저장
        for keyword, count in keywords:
            query = "INSERT INTO popular_keywords (keyword, count) VALUES (%s, %s)"
            cursor.execute(query, (keyword, count))

        connection.commit()

    except Exception as e:
        print(f"DB 저장 오류: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

# 키워드 추출 및 사용자 사전 기반 필터링
def extract_popular_keywords(data, user_dict):
#     komoran = Komoran('user_dict.txt')
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

# 메인 실행
if __name__ == "__main__":
    # 1. 사용자 정의 사전 로드
    user_dict_path = 'user_dict.txt'
    user_dict = load_user_dictionary(user_dict_path)
#     print(user_dict)

    if not user_dict:
        print("사용자 사전을 로드하지 못했습니다.")
    else:
        # 2. DB에서 데이터 가져오기
        data = fetch_data_from_db()

        if data:
            # 3. 사용자 사전 기반 인기 키워드 추출
            popular_keywords = extract_popular_keywords(data, user_dict)

            # 4. 결과 출력
            print("인기 키워드:")
            for keyword, count in popular_keywords:
                print(f"{keyword}: {count}회")

#             # 5. DB에 인기 키워드 저장
            save_keywords_to_db(popular_keywords)
            # JSON 형식으로 결과 출력
            print(json.dumps(popular_keywords, ensure_ascii=False, indent=4))
        else:
            print(json.dumps({"error": "데이터를 가져오지 못했습니다."}, ensure_ascii=False))
