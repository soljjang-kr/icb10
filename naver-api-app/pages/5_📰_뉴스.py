"""
네이버 뉴스 검색 API를 분석하는 대시보드 페이지입니다.

주요 기능:
- 입력 키워드로 관련 뉴스 데이터 수집
- 기사 작성 시간(pubDate) 파싱 및 일자별/시간별 발행량 분석
- 뉴스 본문 링크 도메인 추출을 통한 언론사(도메인) 분포 분석 (바 차트)
- HTML 태그 정제 및 데이터프레임 가공
- 수집 뉴스 상세 표 정보 및 CSV 내보내기 지원
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from urllib.parse import urlparse
from utils.naver_api import fetch_search_api


def clean_html(raw_html):
    """HTML 태그 제거"""
    cleanr = re.compile("<.*?>")
    cleantext = re.sub(cleanr, "", raw_html)
    return cleantext


def get_domain(url):
    """URL에서 도메인 추출"""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return "알 수 없음"


def main():
    st.set_page_config(
        page_title="뉴스 검색 분석",
        page_icon="📰",
        layout="wide",
    )

    st.title("📰 뉴스 검색 분석")
    st.markdown("네이버 뉴스 검색 API를 활용하여 검색 키워드와 관련된 뉴스 보도 현황 및 미디어 동향을 분석합니다.")
    st.markdown("---")

    # API 키 확인
    client_id = st.session_state.get("naver_client_id", "")
    client_secret = st.session_state.get("naver_client_secret", "")

    if not client_id or not client_secret:
        st.warning("⚠️ 메인 페이지(app.py)에서 **Naver API Key**를 먼저 입력해 주세요.")
        return

    # 분석 설정 UI
    with st.sidebar.form("news_form"):
        st.subheader("⚙️ 분석 설정")
        
        query = st.text_input("검색어", value="인공지능")
        display = st.slider("수집 개수", min_value=10, max_value=100, value=100, step=10)
        sort = st.selectbox(
            "정렬 방식",
            options=["sim", "date"],
            format_func=lambda x: {"sim": "유사도순", "date": "날짜순"}.get(x, x),
        )

        submitted = st.form_submit_button("뉴스 데이터 수집")

    if submitted:
        if not query.strip():
            st.error("❌ 검색어를 입력해 주세요.")
            return

        with st.spinner("뉴스 데이터 수집 중..."):
            data = fetch_search_api(
                client_id=client_id,
                client_secret=client_secret,
                endpoint="news",
                query=query,
                display=display,
                sort=sort,
            )

        if "error" in data:
            st.error(data["error"])
            return

        items = data.get("items", [])
        if not items:
            st.info("검색 결과가 없습니다.")
            return

        # 데이터프레임 변환
        df = pd.DataFrame(items)

        # HTML 태그 제거
        df["title_clean"] = df["title"].apply(clean_html)
        df["description_clean"] = df["description"].apply(clean_html)

        # 날짜 파싱 (RFC 822 포맷 등 대응: 예: "Mon, 08 Jun 2026 12:00:00 +0900")
        df["pubDate_dt"] = pd.to_datetime(df["pubDate"], errors="coerce")
        df["pubDate_date"] = df["pubDate_dt"].dt.strftime("%Y-%m-%d")
        df["pubDate_hour"] = df["pubDate_dt"].dt.hour

        # 도메인 추출을 이용한 미디어 분산도 파악
        df["domain"] = df["originallink"].apply(get_domain)

        st.subheader("📊 뉴스 요약 통계")
        total_items = len(df)
        unique_domains = df["domain"].nunique()

        col1, col2 = st.columns(2)
        col1.metric("총 수집 뉴스 기사 수", f"{total_items}개")
        col2.metric("보도한 고유 도메인(언론사) 수", f"{unique_domains}개")

        st.markdown("---")

        row1_col1, row1_col2 = st.columns(2)

        with row1_col1:
            st.subheader("📅 보도 일자별 분포")
            date_counts = df["pubDate_date"].value_counts().reset_index()
            date_counts.columns = ["보도일", "기사 수"]
            date_counts = date_counts.sort_values(by="보도일")

            fig_date = px.bar(
                date_counts,
                x="보도일",
                y="기사 수",
                title="일자별 뉴스 기사 보도 건수",
                template="plotly_dark",
            )
            st.plotly_chart(fig_date, use_container_width=True)

        with row1_col2:
            st.subheader("🕒 시간대별 보도 분포")
            # 시간대(0~23) 카운트
            hour_counts = df["pubDate_hour"].value_counts().reset_index()
            hour_counts.columns = ["시간(시)", "기사 수"]
            hour_counts = hour_counts.sort_values(by="시간(시)")

            fig_hour = px.line(
                hour_counts,
                x="시간(시)",
                y="기사 수",
                markers=True,
                title="보도 등록 시간대별 분포",
                template="plotly_dark",
            )
            st.plotly_chart(fig_hour, use_container_width=True)

        st.markdown("---")

        # 언론사 도메인 분포 시각화
        st.subheader("📰 많이 보도한 언론사 도메인 TOP 15")
        # naver news 도메인은 대행 역할일 경우가 많아 구분 가능하지만 일단 전체 표시
        domain_counts = df["domain"].value_counts().head(15).reset_index()
        domain_counts.columns = ["도메인", "기사 수"]

        fig_domain = px.bar(
            domain_counts,
            x="기사 수",
            y="도메인",
            orientation="h",
            title="언론사별 관련 뉴스 분포",
            template="plotly_dark",
        )
        fig_domain.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_domain, use_container_width=True)

        st.markdown("---")

        # 뉴스 리스트 테이블
        st.subheader("📂 수집 뉴스 기사 상세 목록")
        display_df = df[
            [
                "title_clean",
                "description_clean",
                "domain",
                "pubDate_date",
                "originallink",
            ]
        ].copy()
        display_df.columns = [
            "기사 제목",
            "내용 요약",
            "언론사 도메인",
            "보도일",
            "원문 링크",
        ]
        st.dataframe(display_df, use_container_width=True)

        # CSV 다운로드
        csv = display_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 뉴스 데이터 CSV 다운로드",
            data=csv,
            file_name=f"naver_news_{query}_{sort}.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
