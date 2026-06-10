"""
네이버 블로그 검색 API를 활용하여 데이터를 분석하는 대시보드 페이지입니다.

주요 기능:
- 입력 키워드로 블로그 검색 데이터 수집
- 수집된 블로그 포스팅의 날짜별 분포 추이 시각화
- 인기 블로거(자주 노출되는 블로거) 순위 분석
- HTML 태그 정제 처리 함수 내장
- 포스팅 목록 조회 및 CSV 형식 다운로드 기능
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from utils.naver_api import fetch_search_api


def clean_html(raw_html):
    """HTML 태그 제거"""
    cleanr = re.compile("<.*?>")
    cleantext = re.sub(cleanr, "", raw_html)
    return cleantext


def main():
    st.set_page_config(
        page_title="블로그 검색 분석",
        page_icon="📝",
        layout="wide",
    )

    st.title("📝 블로그 검색 분석")
    st.markdown("네이버 블로그 검색 API를 활용하여 검색 키워드 관련 블로그 포스팅 동향을 파악합니다.")
    st.markdown("---")

    # API 키 확인 (사이드바 렌더링)
    from utils.naver_api import render_api_sidebar
    client_id, client_secret = render_api_sidebar()

    if not client_id or not client_secret:
        st.warning("⚠️ 왼쪽 사이드바에서 **Naver API Key**를 먼저 입력해 주세요.")
        return

    # 분석 설정 UI
    with st.sidebar.form("blog_form"):
        st.subheader("⚙️ 분석 설정")
        
        query = st.text_input("검색어", value="캠핑장 추천")
        display = st.slider("수집 개수", min_value=10, max_value=100, value=100, step=10)
        sort = st.selectbox(
            "정렬 방식",
            options=["sim", "date"],
            format_func=lambda x: {"sim": "유사도순", "date": "날짜순"}.get(x, x),
        )

        submitted = st.form_submit_button("블로그 데이터 수집")

    if submitted:
        if not query.strip():
            st.error("❌ 검색어를 입력해 주세요.")
            return

        with st.spinner("블로그 데이터 수집 중..."):
            data = fetch_search_api(
                client_id=client_id,
                client_secret=client_secret,
                endpoint="blog",
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

        # 날짜 포맷 변환 (YYYYMMDD -> YYYY-MM-DD)
        df["postdate_dt"] = pd.to_datetime(df["postdate"], format="%Y%m%d", errors="coerce")
        df["postdate_str"] = df["postdate_dt"].dt.strftime("%Y-%m-%d")

        # 레이아웃 구성
        st.subheader("📊 블로그 요약 통계")
        total_items = len(df)
        
        # 날짜 범위 구하기
        min_date = df["postdate_dt"].min()
        max_date = df["postdate_dt"].max()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("총 노출 글 개수", f"{total_items}개")
        col2.metric("가장 오래된 글", min_date.strftime("%Y-%m-%d") if pd.notnull(min_date) else "-")
        col3.metric("가장 최근 글", max_date.strftime("%Y-%m-%d") if pd.notnull(max_date) else "-")

        st.markdown("---")

        row1_col1, row1_col2 = st.columns(2)

        with row1_col1:
            st.subheader("📅 작성 날짜별 분포")
            date_counts = df["postdate_str"].value_counts().reset_index()
            date_counts.columns = ["작성일", "발행 건수"]
            date_counts = date_counts.sort_values(by="작성일")

            fig_date = px.bar(
                date_counts,
                x="작성일",
                y="발행 건수",
                title="일자별 블로그 포스팅 발행량 분포 (검색 데이터 기준)",
                template="plotly_dark",
            )
            st.plotly_chart(fig_date, use_container_width=True)

        with row1_col2:
            st.subheader("👑 주요 블로거 TOP 10")
            blogger_counts = df["bloggername"].value_counts().head(10).reset_index()
            blogger_counts.columns = ["블로거명", "노출 횟수"]

            fig_blogger = px.bar(
                blogger_counts,
                x="노출 횟수",
                y="블로거명",
                orientation="h",
                title="상위 노출 블로거 분포",
                template="plotly_dark",
            )
            fig_blogger.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_blogger, use_container_width=True)

        st.markdown("---")

        # 블로그 글 테이블
        st.subheader("📂 수집 블로그 상세 목록")
        display_df = df[
            [
                "title_clean",
                "description_clean",
                "bloggername",
                "postdate_str",
                "link",
            ]
        ].copy()
        display_df.columns = [
            "글 제목",
            "내용 요약",
            "블로거명",
            "작성일",
            "링크",
        ]
        st.dataframe(display_df, use_container_width=True)

        # CSV 다운로드
        csv = display_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 블로그 데이터 CSV 다운로드",
            data=csv,
            file_name=f"naver_blog_{query}_{sort}.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
