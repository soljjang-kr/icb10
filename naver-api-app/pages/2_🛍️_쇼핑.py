"""
네이버 쇼핑 API를 분석하는 대시보드 페이지입니다.

주요 기능:
- 입력된 키워드로 네이버 쇼핑 상품 데이터 수집
- 최저가 기준 가격 분포 히스토그램 시각화
- 주요 판매 몰(mallName) 및 브랜드(brand) 분포 분석 (바 차트)
- 상품명 정제 및 가격 통계 지표(평균, 최소, 최대값) 표시
- 수집된 상품 목록 테이블 및 CSV 다운로드 제공
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from utils.naver_api import fetch_search_api


def clean_html(raw_html):
    """HTML 태그 제거 함수 (네이버 API는 상품명에 <b> 태그 등을 포함함)"""
    cleanr = re.compile("<.*?>")
    cleantext = re.sub(cleanr, "", raw_html)
    return cleantext


def main():
    st.set_page_config(
        page_title="쇼핑 검색 분석",
        page_icon="🛍️",
        layout="wide",
    )

    st.title("🛍️ 쇼핑 검색 분석")
    st.markdown("네이버 쇼핑 API를 검색하여 최신 상품 정보, 가격 통계 및 입점몰 분포를 분석합니다.")
    st.markdown("---")

    # API 키 확인 (사이드바 렌더링)
    from utils.naver_api import render_api_sidebar
    client_id, client_secret = render_api_sidebar()

    if not client_id or not client_secret:
        st.warning("⚠️ 왼쪽 사이드바에서 **Naver API Key**를 먼저 입력해 주세요.")
        return

    # 분석 설정 UI
    with st.sidebar.form("shop_form"):
        st.subheader("⚙️ 분석 설정")
        
        query = st.text_input("검색어", value="무선 이어폰")
        display = st.slider("수집 개수", min_value=10, max_value=100, value=50, step=10)
        sort = st.selectbox(
            "정렬 방식",
            options=["sim", "date", "asc", "dsc"],
            format_func=lambda x: {
                "sim": "유사도순",
                "date": "날짜순",
                "asc": "가격 오름차순",
                "dsc": "가격 내림차순",
            }.get(x, x),
        )

        submitted = st.form_submit_button("쇼핑 데이터 수집")

    if submitted:
        if not query.strip():
            st.error("❌ 검색어를 입력해 주세요.")
            return

        with st.spinner("쇼핑 상품 데이터 수집 중..."):
            data = fetch_search_api(
                client_id=client_id,
                client_secret=client_secret,
                endpoint="shop",
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

        # 데이터 프레임 변환
        df = pd.DataFrame(items)

        # 상품명 HTML 태그 제거
        df["title_clean"] = df["title"].apply(clean_html)

        # 가격 데이터 정수화
        df["lprice"] = pd.to_numeric(df["lprice"], errors="coerce")
        df = df.dropna(subset=["lprice"])  # 가격이 없는 제품 제외

        # 주요 요약 정보 (Metrics)
        st.subheader("📊 가격 통계 지표")
        avg_price = df["lprice"].mean()
        min_price = df["lprice"].min()
        max_price = df["lprice"].max()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("총 수집 상품 수", f"{len(df)}개")
        col2.metric("평균 가격", f"{avg_price:,.0f}원")
        col3.metric("최저 가격", f"{min_price:,.0f}원")
        col4.metric("최고 가격", f"{max_price:,.0f}원")

        st.markdown("---")

        # 시각화 영역 (2x2 그리드)
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)

        with row1_col1:
            st.subheader("💵 가격 분포")
            fig_price = px.histogram(
                df,
                x="lprice",
                nbins=20,
                title="상품 가격대 분포",
                labels={"lprice": "가격 (원)", "count": "상품 수"},
                template="plotly_dark",
            )
            st.plotly_chart(fig_price, use_container_width=True)

        with row1_col2:
            st.subheader("🏬 입점 몰 분포 (Top 10)")
            mall_counts = df["mallName"].value_counts().head(10).reset_index()
            mall_counts.columns = ["쇼핑몰", "상품 수"]
            fig_mall = px.bar(
                mall_counts,
                x="상품 수",
                y="쇼핑몰",
                orientation="h",
                title="상위 입점 몰 분포",
                template="plotly_dark",
            )
            fig_mall.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_mall, use_container_width=True)

        with row2_col1:
            st.subheader("🏷️ 브랜드 분포 (Top 10)")
            # 결측치나 빈 문자열 브랜드 제외
            brand_df = df[df["brand"].str.strip() != ""]
            if not brand_df.empty:
                brand_counts = brand_df["brand"].value_counts().head(10).reset_index()
                brand_counts.columns = ["브랜드", "상품 수"]
                fig_brand = px.bar(
                    brand_counts,
                    x="상품 수",
                    y="브랜드",
                    orientation="h",
                    title="상위 브랜드 분포",
                    template="plotly_dark",
                )
                fig_brand.update_layout(yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig_brand, use_container_width=True)
            else:
                st.info("수집된 상품 중 브랜드 정보가 존재하지 않습니다.")

        with row2_col2:
            st.subheader("🏷️ 카테고리 분포 (대분류)")
            category_counts = df["category2"].value_counts().head(10).reset_index()
            category_counts.columns = ["카테고리", "상품 수"]
            fig_cat = px.pie(
                category_counts,
                values="상품 수",
                names="카테고리",
                title="상위 카테고리 구성 비율",
                template="plotly_dark",
            )
            st.plotly_chart(fig_cat, use_container_width=True)

        st.markdown("---")

        # 테이블 및 다운로드
        st.subheader("📂 상품 상세 목록")
        display_df = df[
            ["title_clean", "lprice", "mallName", "brand", "maker", "link"]
        ].copy()
        display_df.columns = [
            "상품명",
            "최저가(원)",
            "판매처",
            "브랜드",
            "제조사",
            "링크",
        ]
        st.dataframe(display_df, use_container_width=True)

        # CSV 다운로드
        csv = display_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 쇼핑 데이터 CSV 다운로드",
            data=csv,
            file_name=f"naver_shopping_{query}_{sort}.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
