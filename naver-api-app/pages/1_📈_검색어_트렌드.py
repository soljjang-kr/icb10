"""
네이버 데이터랩 통합 검색어 트렌드 API를 분석하는 대시보드 페이지입니다.

주요 기능:
- 여러 키워드를 쉼표(,)로 입력받아 각각의 검색 트렌드 비교 분석
- 검색 기간(시작일, 종료일), 조회 단위(일간, 주간, 월간) 필터 설정
- 성별 및 기기별 필터 기능 제공
- Plotly를 활용한 인터랙티브 선 차트 시각화 및 데이터 다운로드 지원
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils.naver_api import fetch_datalab_search


def main():
    st.set_page_config(
        page_title="검색어 트렌드 분석",
        page_icon="📈",
        layout="wide",
    )

    st.title("📈 네이버 검색어 트렌드 분석")
    st.markdown("네이버에서 검색되는 특정 키워드 그룹의 상대적 트렌드를 비교 분석합니다.")
    st.markdown("---")

    # API 키 확인 (사이드바 렌더링)
    from utils.naver_api import render_api_sidebar
    client_id, client_secret = render_api_sidebar()

    if not client_id or not client_secret:
        st.warning("⚠️ 왼쪽 사이드바에서 **Naver API Key**를 먼저 입력해 주세요.")
        return

    # 분석 설정 UI
    with st.sidebar.form("trend_form"):
        st.subheader("⚙️ 분석 설정")
        
        # 키워드 입력
        keywords_input = st.text_input(
            "검색 키워드 (쉼표로 구분)",
            value="아이폰, 갤럭시",
            help="비교할 키워드들을 쉼표(,)로 구분하여 입력하세요 (최대 5개 그룹).",
        )
        
        # 날짜 범위 설정
        today = datetime.today()
        start_date = st.date_input("시작일", today - timedelta(days=365))
        end_date = st.date_input("종료일", today)
        
        # 단위 선택
        time_unit = st.selectbox("조회 단위", ["date", "week", "month"], index=0)
        
        # 성별/기기 필터
        device = st.selectbox("기기", ["전체", "PC", "모바일"], index=0)
        gender = st.selectbox("성별", ["전체", "남성", "여성"], index=0)

        # 제출 버튼
        submitted = st.form_submit_button("트렌드 조회")

    if submitted:
        # 키워드 전처리
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
        if not keywords:
            st.error("❌ 최소 한 개 이상의 키워드를 입력해 주세요.")
            return
        if len(keywords) > 5:
            st.warning("⚠️ 네이버 API 제약으로 인해 상위 5개 키워드만 분석합니다.")
            keywords = keywords[:5]

        # API 전송을 위한 키워드 그룹 포맷 구성
        # 각 키워드를 각각의 그룹명으로 매핑하여 트렌드 비교가 가능하도록 설정
        keyword_groups = [{"groupName": kw, "keywords": [kw]} for kw in keywords]

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

        # 로딩 스피너
        with st.spinner("네이버 API 호출 중..."):
            data = fetch_datalab_search(
                client_id=client_id,
                client_secret=client_secret,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                time_unit=time_unit,
                keyword_groups=keyword_groups,
                device=device_val,
                gender=gender_val,
            )

        # 에러 처리
        if "error" in data:
            st.error(data["error"])
            return

        # 데이터 가공
        results = data.get("results", [])
        if not results:
            st.info("조회된 데이터가 없습니다.")
            return

        # 모든 데이터를 하나의 DataFrame으로 통합
        df_list = []
        for res in results:
            title = res.get("title")
            items = res.get("data", [])
            if items:
                temp_df = pd.DataFrame(items)
                temp_df["keyword"] = title
                df_list.append(temp_df)

        if not df_list:
            st.warning("❌ 선택 기간 내에 수집된 데이터 포인트가 없습니다.")
            return

        df = pd.concat(df_list, ignore_index=True)
        # 컬럼 이름 변경 및 날짜 형변환
        df["period"] = pd.to_datetime(df["period"])
        df["ratio"] = pd.to_numeric(df["ratio"])

        # 넓은 포맷으로 변환하여 표로 표시하기 편하게 제작
        df_pivot = df.pivot(index="period", columns="keyword", values="ratio").reset_index()

        st.subheader("📊 트렌드 시각화")
        st.markdown(
            "가장 검색량이 많았던 시점의 수치를 100으로 설정한 **상대적 검색량 비율**입니다."
        )

        # Plotly 차트 생성
        fig = px.line(
            df,
            x="period",
            y="ratio",
            color="keyword",
            title="기간별 검색량 트렌드",
            labels={"period": "날짜", "ratio": "상대적 비율 (Max=100)", "keyword": "키워드"},
            template="plotly_dark",
        )
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # 데이터 요약 정보
        st.subheader("📝 키워드별 통계 요약")
        summary_data = []
        for kw in keywords:
            kw_df = df[df["keyword"] == kw]
            if not kw_df.empty:
                summary_data.append(
                    {
                        "키워드": kw,
                        "평균 비율": round(kw_df["ratio"].mean(), 2),
                        "최대 비율": kw_df["ratio"].max(),
                        "최소 비율": kw_df["ratio"].min(),
                    }
                )
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)

        # 데이터 세부 보기 및 다운로드
        st.subheader("📂 세부 데이터 데이터프레임")
        st.dataframe(df_pivot, use_container_width=True)

        # CSV 다운로드 버튼
        csv = df_pivot.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 CSV 데이터 다운로드",
            data=csv,
            file_name=f"naver_search_trend_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
