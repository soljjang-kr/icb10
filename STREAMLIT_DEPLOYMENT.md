# Streamlit 배포 가이드

이 프로젝트의 Streamlit 앱은 `naver-api-app` 폴더 안에 있습니다.

## 1. GitHub에 push

Streamlit Community Cloud는 GitHub 저장소를 기준으로 앱을 배포합니다.

```powershell
git add naver-api-app STREAMLIT_DEPLOYMENT.md
git commit -m "Prepare Streamlit deployment"
git push
```

## 2. Streamlit Community Cloud 설정

Streamlit Cloud에서 새 앱을 만들 때 다음처럼 설정하세요.

- Repository: 이 프로젝트가 올라간 GitHub 저장소
- Branch: 배포할 브랜치, 예: `main`
- Main file path: `naver-api-app/app.py`

`requirements.txt`는 앱 진입 파일과 같은 폴더인 `naver-api-app/requirements.txt`에 이미 있습니다.

## 3. Secrets 설정

앱 생성 화면의 Advanced settings 또는 배포 후 App settings > Secrets에 아래 형식으로 입력하세요.

```toml
NAVER_CLIENT_ID = "발급받은_네이버_Client_ID"
NAVER_CLIENT_SECRET = "발급받은_네이버_Client_Secret"
```

선택적으로 Claude 분석 기능을 연결한다면 다음 값도 추가할 수 있습니다.

```toml
ANTHROPIC_API_KEY = "발급받은_Anthropic_API_Key"
```

Secrets 값은 Git에 커밋하지 않습니다.

## 4. 로컬 실행 확인

로컬에서 먼저 확인하려면:

```powershell
cd naver-api-app
streamlit run app.py
```

로컬 `.env`를 쓰는 경우 `naver-api-app/.env`에 아래처럼 둘 수 있습니다. 이 파일은 `.gitignore`에 의해 커밋되지 않습니다.

```env
NAVER_CLIENT_ID=발급받은_네이버_Client_ID
NAVER_CLIENT_SECRET=발급받은_네이버_Client_Secret
```
