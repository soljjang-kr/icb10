"""
네이버 카페글 검색 API를 분석하는 대시보드 페이지입니다.

주요 기능:
- 입력 키워드로 네이버 카페 게시글 수집
- 수집된 글 중 상위 카페명(cafename) 분포 분석 및 시각화 (바 차트)
- HTML 태그 제거 및 데이터 가공 제공
- 게시글 상세 목록 및 CSV 다운로드 지원
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
        page_title="카페글 검색 분석",
        page_icon="☕",
        layout="wide",
    )

    st.title("☕ 카페글 검색 분석")
    st.markdown("네이버 카페글 검색 API를 활용하여 관련 키워드가 언급된 주요 네이버 카페와 게시글을 분석합니다.")
    st.markdown("---")

    # API 키 확인
    client_id = st.session_state.get("naver_client_id", "")
    client_secret = st.session_state.get("naver_client_secret", "")

    if not client_id or not client_secret:
        st.warning("⚠️ 메인 페이지(app.py)에서 **Naver API Key**를 먼저 입력해 주세요.")
        return

    # 분석 설정 UI
    with st.sidebar.form("cafe_form"):
        st.subheader("⚙️ 분석 설정")
        
        query = st.text_input("검색어", value="맥북 추천")
        display = st.slider("수집 개수", min_value=10, max_value=100, value=50, step=10)
        sort = st.selectbox(
            "정렬 방식",
            options=["sim", "date"],
            format_func=lambda x: {"sim": "유사도순", "date": "날짜순"}.get(x, x),
        )

        submitted = st.form_submit_button("카페글 데이터 수집")

    if submitted:
        if not query.strip():
            st.error("❌ 검색어를 입력해 주세요.")
            return

        with st.spinner("카페글 데이터 수집 중..."):
            data = fetch_search_api(
                client_id=client_id,
                client_secret=client_secret,
                endpoint="cafearticle",
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

        # 카페 요약 지표
        st.subheader("📊 카페글 분석 통계")
        total_items = len(df)
        unique_cafes = df["cafename"].nunique()

        col1, col2 = st.columns(2)
        col1.metric("수집된 게시글 수", f"{total_items}개")
        col2.metric("글이 수집된 고유 카페 수", f"{unique_cafes}개")

        st.markdown("---")

        # 시각화: 어떤 카페에 글이 많이 작성되었는지 분석
        st.subheader("☕ 언급량이 가장 많은 네이버 카페 TOP 15")
        cafe_counts = df["cafename"].value_counts().head(15).reset_index()
        cafe_counts.columns = ["카페명", "게시글 수"]

        fig_cafe = px.bar(
            cafe_counts,
            x="게시글 수",
            y="카페명",
            orientation="h",
            title="카페별 관련 글 노출 횟수",
            template="plotly_dark",
        )
        fig_cafe.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_cafe, use_container_width=True)

        st.markdown("---")

        # 카페글 테이블
        st.subheader("📂 수집 카페글 상세 목록")
        display_df = df[
            [
                "title_clean",
                "description_clean",
                "cafename",
                "link",
            ]
        ].copy()
        display_df.columns = [
            "글 제목",
            "내용 요약",
            "카페명",
            "링크",
        ]
        st.dataframe(display_df, use_container_width=True)

        # CSV 다운로드
        csv = display_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 카페글 데이터 CSV 다운로드",
            data=csv,
            file_name=f"naver_cafe_{query}_{sort}.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
