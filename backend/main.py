from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chat import get_answer
from hot_keyword import load_user_dictionary, extract_popular_keywords, fetch_location_from_db, fetch_data_from_db, update_popular_keywords, save_keywords_to_db, start_scheduler


app = FastAPI()

# 최초 실행시 키워드 추출
update_popular_keywords()
# 스케줄러 시작
start_scheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 요청 모델 정의
class QuestionRequest(BaseModel):
    question: str

# 답변 생성 엔드포인트


@app.post("/get_answer")
async def answer_question(request: QuestionRequest):
    try:
        answer = get_answer(request.question)
        return {"question": request.question, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 인기 키워드 추출 API 엔드포인트
@app.get("/hot_keywords")
async def extract_keywords():
    try:
        # 사용자 사전 로드
        user_dict_path = '/app/data/user_dict.txt'
        user_dict = load_user_dictionary(user_dict_path)

        if not user_dict:
            raise HTTPException(status_code=500, detail="사용자 사전을 로드하지 못했습니다.")

        # DB에서 locations 데이터 가져오기
        locations = fetch_location_from_db()

        if not locations:
            raise HTTPException(status_code=500, detail="DB에서 locations 데이터를 가져올 수 없습니다.")

        for location in locations:
            # DB에서 데이터 가져오기
            data = fetch_data_from_db(location)

            if not data:
                raise HTTPException(status_code=500, detail="DB에서 데이터를 가져올 수 없습니다.")

            # 인기 키워드 추출
            popular_keywords = extract_popular_keywords(data, user_dict)

            # DB에 인기 키워드 저장
            save_keywords_to_db(popular_keywords, location)

        # JSON 형식으로 결과 출력
        return {"popular_keywords": popular_keywords}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
