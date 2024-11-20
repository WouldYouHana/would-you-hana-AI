# would-you-hana-AI
📁 우주하나 AI 레포지토리

- API 명세 : https://www.notion.so/API-11f6edd1e95780f28248c14e54e34288

# 사용법

1. **config 폴더 생성**
2. `.env` 파일 생성  
   - API 키 설정  
   - 예시: `hana = OPENAI_API_KEY`
3. 가상환경 생성
4. **라이브러리 설치**
   ```bash
   pip install -r requirements.txt
5. cd backend
```bash
   uvicorn main:app --reload
