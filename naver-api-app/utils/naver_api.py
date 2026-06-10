"""
네이버 Open API 호출을 위한 유틸리티 함수 모음입니다.

주요 기능:
- 검색어 트렌드 API (Datalab Search) 호출
- 쇼핑 검색 API 호출
- 블로그 검색 API 호출
- 카페글 검색 API 호출
- 뉴스 검색 API 호출
- 쇼핑 트렌드 API (Datalab Shopping Insight) 호출
- 공통 헤더 설정 및 오류 처리 포함
"""

import requests
import json
import os
import streamlit as st
from pathlib import Path
from typing import Optional


# 네이버 API 기본 URL
NAVER_API_BASE = "https://openapi.naver.com/v1"


def naver_request(method: str, url: str, **kwargs) -> requests.Response:
    session = requests.Session()
    session.trust_env = False
    return session.request(method, url, **kwargs)


def load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip().strip('"').strip("'")


load_local_env()


def render_api_sidebar():
    """
    모든 페이지의 사이드바에 공통으로 네이버 API Key 입력창을 렌더링하고
    세션 상태를 업데이트하여 반환합니다.
    """
    st.sidebar.title("🔑 API 설정")
    st.sidebar.markdown("네이버 개발자 센터에서 발급받은 API 키를 입력해 주세요.")
    
    env_client_id = os.getenv("NAVER_CLIENT_ID", "")
    env_client_secret = os.getenv("NAVER_CLIENT_SECRET", "")

    if not st.session_state.get("naver_client_id"):
        st.session_state.naver_client_id = env_client_id
    if not st.session_state.get("naver_client_secret"):
        st.session_state.naver_client_secret = env_client_secret
    if not st.session_state.get("sidebar_client_id"):
        st.session_state.sidebar_client_id = st.session_state.naver_client_id
    if not st.session_state.get("sidebar_client_secret"):
        st.session_state.sidebar_client_secret = st.session_state.naver_client_secret

    client_id = st.sidebar.text_input(
        "Naver Client ID",
        type="password",
        help="네이버 오픈 API Client ID를 입력하세요.",
        key="sidebar_client_id"
    )
    client_secret = st.sidebar.text_input(
        "Naver Client Secret",
        type="password",
        help="네이버 오픈 API Client Secret을 입력하세요.",
        key="sidebar_client_secret"
    )

    st.session_state.naver_client_id = client_id
    st.session_state.naver_client_secret = client_secret
    return client_id, client_secret


def get_headers(client_id: str, client_secret: str) -> dict:
    """
    네이버 API 인증 헤더를 반환합니다.

    Args:
        client_id: 네이버 개발자 센터에서 발급받은 Client ID
        client_secret: 네이버 개발자 센터에서 발급받은 Client Secret

    Returns:
        HTTP 요청에 사용할 헤더 딕셔너리
    """
    return {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json",
    }


def fetch_datalab_search(
    client_id: str,
    client_secret: str,
    start_date: str,
    end_date: str,
    time_unit: str,
    keyword_groups: list,
    device: str = "",
    gender: str = "",
    ages: list = None,
) -> dict:
    """
    네이버 데이터랩 통합 검색어 트렌드 API를 호출합니다.

    Args:
        client_id: 네이버 Client ID
        client_secret: 네이버 Client Secret
        start_date: 조회 시작일 (YYYY-MM-DD)
        end_date: 조회 종료일 (YYYY-MM-DD)
        time_unit: 기간 단위 (date | week | month)
        keyword_groups: 키워드 그룹 리스트 [{"groupName": "...", "keywords": ["..."]}]
        device: 기기 필터 ('' | 'pc' | 'mo')
        gender: 성별 필터 ('' | 'm' | 'f')
        ages: 나이 필터 리스트 (['1','2',...])

    Returns:
        API 응답 딕셔너리, 오류 시 {"error": "..."}
    """
    url = f"{NAVER_API_BASE}/datalab/search"
    headers = get_headers(client_id, client_secret)
    headers["Content-Type"] = "application/json"

    payload = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": keyword_groups,
    }
    if device:
        payload["device"] = device
    if gender:
        payload["gender"] = gender
    if ages:
        payload["ages"] = ages

    try:
        response = naver_request(
            "POST",
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP 오류: {e.response.status_code} - {e.response.text}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"요청 오류: {str(e)}"}


def fetch_search_api(
    client_id: str,
    client_secret: str,
    endpoint: str,
    query: str,
    display: int = 100,
    start: int = 1,
    sort: str = "sim",
) -> dict:
    """
    네이버 검색 API (블로그/뉴스/카페/쇼핑)를 호출합니다.

    Args:
        client_id: 네이버 Client ID
        client_secret: 네이버 Client Secret
        endpoint: API 엔드포인트 경로 (예: 'blog', 'news', 'cafearticle', 'shop')
        query: 검색어
        display: 결과 개수 (최대 100)
        start: 검색 시작 위치
        sort: 정렬 방식 (sim: 정확도순, date: 날짜순)

    Returns:
        API 응답 딕셔너리, 오류 시 {"error": "..."}
    """
    url = f"{NAVER_API_BASE}/search/{endpoint}.json"
    headers = get_headers(client_id, client_secret)

    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": sort,
    }

    try:
        response = naver_request(
            "GET",
            url,
            headers=headers,
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP 오류: {e.response.status_code} - {e.response.text}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"요청 오류: {str(e)}"}


def fetch_datalab_shopping(
    client_id: str,
    client_secret: str,
    start_date: str,
    end_date: str,
    time_unit: str,
    category: list,
    device: str = "",
    gender: str = "",
    ages: list = None,
) -> dict:
    """
    네이버 데이터랩 쇼핑인사이트 카테고리 트렌드 API를 호출합니다.

    Args:
        client_id: 네이버 Client ID
        client_secret: 네이버 Client Secret
        start_date: 조회 시작일 (YYYY-MM-DD)
        end_date: 조회 종료일 (YYYY-MM-DD)
        time_unit: 기간 단위 (date | week | month)
        category: 카테고리 리스트 [{"name": "...", "param": ["50000167"]}]
        device: 기기 필터
        gender: 성별 필터
        ages: 나이 필터

    Returns:
        API 응답 딕셔너리, 오류 시 {"error": "..."}
    """
    url = f"{NAVER_API_BASE}/datalab/shopping/categories"
    headers = get_headers(client_id, client_secret)
    headers["Content-Type"] = "application/json"

    payload = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "category": category,
    }
    if device:
        payload["device"] = device
    if gender:
        payload["gender"] = gender
    if ages:
        payload["ages"] = ages

    try:
        response = naver_request(
            "POST",
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP 오류: {e.response.status_code} - {e.response.text}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"요청 오류: {str(e)}"}


def fetch_datalab_shopping_keyword(
    client_id: str,
    client_secret: str,
    start_date: str,
    end_date: str,
    time_unit: str,
    category: str,
    keyword: list,
    device: str = "",
    gender: str = "",
    ages: list = None,
) -> dict:
    """
    네이버 데이터랩 쇼핑인사이트 키워드 트렌드 API를 호출합니다.

    Args:
        category: 쇼핑 카테고리 ID
        keyword: 키워드 그룹 리스트 [{"name": "...", "param": ["키워드"]}]

    Returns:
        API 응답 딕셔너리, 오류 시 {"error": "..."}
    """
    url = f"{NAVER_API_BASE}/datalab/shopping/category/keywords"
    headers = get_headers(client_id, client_secret)
    headers["Content-Type"] = "application/json"

    payload = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "category": category,
        "keyword": keyword,
    }
    if device:
        payload["device"] = device
    if gender:
        payload["gender"] = gender
    if ages:
        payload["ages"] = ages

    try:
        response = naver_request(
            "POST",
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP 오류: {e.response.status_code} - {e.response.text}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"요청 오류: {str(e)}"}
