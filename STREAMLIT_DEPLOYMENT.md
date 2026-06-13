# Streamlit 배포 가이드

이 프로젝트의 Streamlit 앱은 `naver-api-app` 폴더 안에 있습니다.

## 현재 배포 주소

- Streamlit 앱: https://i3sjkmmehw83ms9h2taqua.streamlit.app/

## 현재 프로젝트 작업 내역

- 네이버 Open API 기반 Streamlit 대시보드 앱을 `naver-api-app`에 구성했습니다.
- 검색어 트렌드, 쇼핑 검색, 블로그 검색, 카페글 검색, 뉴스 검색, 쇼핑인사이트 탭을 구현했습니다.
- 네이버 API 키는 로컬 `.env`와 Streamlit Cloud Secrets 양쪽에서 읽을 수 있도록 처리했습니다.
- Streamlit Cloud 배포 환경에서는 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` 값을 Secrets에 등록해 사용하도록 정리했습니다.
- 카페, 뉴스, 쇼핑 트렌드 페이지도 공통 API 설정 사이드바를 사용하도록 수정해 직접 페이지 접속 시에도 API 키가 적용되게 했습니다.
- 검색 API 인증 오류가 발생할 때 네이버 개발자센터의 `검색` API 권한 누락 여부를 확인하도록 안내 메시지를 개선했습니다.
- 커밋 이후 자동으로 GitHub 원격 저장소에 푸시되도록 `.githooks/post-commit` 훅을 설정했습니다.

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

## 4. 네이버 개발자센터 API 권한 확인

이 앱의 전체 탭을 사용하려면 네이버 개발자센터의 같은 애플리케이션에 아래 사용 API가 모두 추가되어 있어야 합니다.

- 검색: 쇼핑, 블로그, 카페글, 뉴스 탭에서 사용
- 데이터랩 (검색어트렌드): 검색어 트렌드 탭에서 사용
- 데이터랩 (쇼핑인사이트): 쇼핑 트렌드 탭에서 사용

`Scope Status Invalid` 또는 `errorCode 024` 오류가 나오면 키가 틀린 것보다, 해당 애플리케이션의 사용 API 목록에 `검색`이 빠진 경우가 많습니다.

## 5. 로컬 실행 확인

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
