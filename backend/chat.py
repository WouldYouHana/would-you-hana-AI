import openai
import faiss
import numpy as np
import pickle
from dotenv import load_dotenv
import os

# OpenAI API 키 설정
load_dotenv(dotenv_path="/app/config/.env")
openai.api_key = os.getenv("hana")

# FAQ 데이터와 임베딩 로드
with open("/app/data/Processed_Data/faq_data2.pkl", "rb") as f:
    faq_data_pd = pickle.load(f)
with open("/app/data/Processed_Data/faq_embeddings2.pkl", "rb") as f:
    faq_embeddings = pickle.load(f)

# FAISS 인덱스 초기화 및 임베딩 추가
dimension = faq_embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(faq_embeddings)

# OpenAI 임베딩 생성 함수


def get_openai_embedding(text: str):
    response = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=text
    )
    return np.array(response['data'][0]['embedding'], dtype='float32')

# 유사 문장 검색 함수


def search_similar_sentence(question: str, threshold: float = 0.5):
    question_embedding = get_openai_embedding(question).reshape(1, -1)
    distances, indices = index.search(question_embedding, 1)

    if distances[0][0] < threshold:
        return faq_data_pd.iloc[indices[0][0]]['Question'], faq_data_pd.iloc[indices[0][0]]['Answer'], True
    else:
        return None, None, False

# GPT-3.5를 통한 답변 생성 함수


def generate_answer_with_gpt(question: str, related_question: str = None, related_answer: str = None):
    messages = [{"role": "system", "content": "당신은 친절한 정보 제공자입니다."}]

    if related_question and related_answer:
        messages.append({
            "role": "system",
            "content": f"관련 질문: {related_question}\n관련 답변: {related_answer}"
        })

    messages.append({"role": "user", "content": question})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=300
    )
    return response['choices'][0]['message']['content']

# 최종 답변 생성 함수


def get_answer(question: str):
    related_question, related_answer, found = search_similar_sentence(question)
    if found:
        return generate_answer_with_gpt(question, related_question, related_answer)
    else:
        return generate_answer_with_gpt(question)
