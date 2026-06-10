"""
네이버 데이터랩 쇼핑인사이트 카테고리 트렌드 API를 분석하는 대시보드 페이지입니다.

주요 기능:
- 네이버 쇼핑 대분류 카테고리를 멀티 선택하여 클릭 트렌드 비교
- 시작일, 종료일, 시간 단위(일간/주간/월간) 및 기기/성별 필터링 기능
- 연령대별 세부 필터링 매핑 구현
- Plotly를 활용한 쇼핑 관심도 선 차트 시각화 및 데이터 다운로드
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils.naver_api import fetch_datalab_shopping

# 네이버 쇼핑 표준 대분류 카테고리 ID 매핑
CATEGORIES = {
    "패션의류": "50000000",
    "패션잡화": "50000001",
    "화장품/미용": "50000002",
    "디지털/가전": "50000003",
    "가구/인테리어": "50000004",
    "출산/육아": "50000005",
    "식품": "50000006",
    "스포츠/레저": "50000007",
    "생활/건강": "50000008",
    "여가/생활편의": "50000009",
    "면세점": "50000010",
    "도서": "50000011",
}

# 네이버 API 연령대 코드 매핑
AGE_MAP = {
    "10대": ["2"],
    "20대": ["3", "4"],
    "30대": ["5", "6"],
    "40대": ["7", "8"],
    "50대": ["9", "10"],
    "60대 이상": ["11"],
}


def main():
    st.set_page_config(
        page_title="쇼핑 트렌드 분석",
        page_icon="📊",
        layout="wide",
    )

    st.title("📊 쇼핑 트렌드 분석 (쇼핑인사이트)")
    st.markdown("네이버 데이터랩 쇼핑인사이트 API를 조회하여 카테고리별 클릭량 트렌드를 다각도로 분석합니다.")
    st.markdown("---")

    # API 키 확인
    client_id = st.session_state.get("naver_client_id", "")
    client_secret = st.session_state.get("naver_client_secret", "")

    if not client_id or not client_secret:
        st.warning("⚠️ 메인 페이지(app.py)에서 **Naver API Key**를 먼저 입력해 주세요.")
        return

    # 분석 설정 UI
    with st.sidebar.form("shopping_trend_form"):
        st.subheader("⚙️ 분석 설정")
        
        # 카테고리 선택 (다중 선택 가능)
        selected_cats = st.multiselect(
            "비교할 쇼핑 카테고리 (최대 5개)",
            options=list(CATEGORIES.keys()),
            default=["패션의류", "디지털/가전"],
            help="클릭 트렌드를 비교 분석할 대분류를 선택하세요.",
        )
        
        # 날짜 범위 설정
        today = datetime.today()
        start_date = st.date_input("시작일", today - timedelta(days=90))
        end_date = st.date_input("종료일", today)
        
        # 단위 선택
        time_unit = st.selectbox("조회 단위", ["date", "week", "month"], index=0)
        
        # 기기 및 성별 필터
        device = st.selectbox("기기", ["전체", "PC", "모바일"], index=0)
        gender = st.selectbox("성별", ["전체", "남성", "여성"], index=0)
        
        # 연령 필터
        selected_ages = st.multiselect(
            "연령대 필터 (미선택 시 전체 연령)",
            options=list(AGE_MAP.keys()),
        )

        submitted = st.form_submit_button("트렌드 조회")

    if submitted:
        if not selected_cats:
            st.error("❌ 최소 한 개 이상의 카테고리를 선택해 주세요.")
            return
        if len(selected_cats) > 5:
            st.warning("⚠️ 네이버 API 제약으로 인해 상위 5개 카테고리만 조회합니다.")
            selected_cats = selected_cats[:5]

        # API 호출 포맷팅
        category_payload = [
            {"name": cat, "param": [CATEGORIES[cat]]} for cat in selected_cats
        ]

        # 필터 값 변환
        device_val = ""
        if device == "PC":
            device_val = "pc"
        elif device == "모바일":
            device_val = "mo"

        gender_val = ""
        if gender == "남성":
            gender_val = "m"
        elif gender == "여성":
            gender_val = "f"

        # 연령 코드 병합
        ages_val = []
        for age in selected_ages:
            ages_val.extend(AGE_MAP[age])
        if not ages_val:
            ages_val = None

        with st.spinner("쇼핑 트렌드 데이터 수집 중..."):
            data = fetch_datalab_shopping(
                client_id=client_id,
                client_secret=client_secret,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                time_unit=time_unit,
                category=category_payload,
                device=device_val,
                gender=gender_val,
                ages=ages_val,
            )

        if "error" in data:
            st.error(data["error"])
            return

        results = data.get("results", [])
        if not results:
            st.info("조회된 데이터가 없습니다.")
            return

        # 데이터프레임 변환
        df_list = []
        for res in results:
            title = res.get("title")
            items = res.get("data", [])
            if items:
                temp_df = pd.DataFrame(items)
                temp_df["category"] = title
                df_list.append(temp_df)

        if not df_list:
            st.warning("❌ 선택 기간 내에 수집된 데이터가 없습니다.")
            return

        df = pd.concat(df_list, ignore_index=True)
        df["period"] = pd.to_datetime(df["period"])
        df["ratio"] = pd.to_numeric(df["ratio"])

        df_pivot = df.pivot(index="period", columns="category", values="ratio").reset_index()

        st.subheader("📊 쇼핑 카테고리별 트렌드")
        st.markdown(
            "조회 기간 내 가장 클릭량이 많았던 시점의 지수를 100으로 설정한 **상대적 클릭 추이**입니다."
        )

        # Plotly 라인 차트 시각화
        fig = px.line(
            df,
            x="period",
            y="ratio",
            color="category",
            title="쇼핑인사이트 카테고리 트렌드",
            labels={"period": "날짜", "ratio": "상대적 클릭 비율 (Max=100)", "category": "카테고리"},
            template="plotly_dark",
        )
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📝 카테고리별 요약 통계")
        summary_data = []
        for cat in selected_cats:
            cat_df = df[df["category"] == cat]
            if not cat_df.empty:
                summary_data.append(
                    {
                        "카테고리": cat,
                        "평균 클릭지수": round(cat_df["ratio"].mean(), 2),
                        "최대 클릭지수": cat_df["ratio"].max(),
                        "최소 클릭지수": cat_df["ratio"].min(),
                    }
                )
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)

        st.subheader("📂 세부 데이터 데이터프레임")
        st.dataframe(df_pivot, use_container_width=True)

        # CSV 다운로드
        csv = df_pivot.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 쇼핑 트렌드 CSV 다운로드",
            data=csv,
            file_name=f"naver_shopping_trend_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
