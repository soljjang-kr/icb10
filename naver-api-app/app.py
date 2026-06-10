"""
네이버 Open API 데이터 분석 대시보드의 메인 진입점 스크립트입니다.

주요 기능:
- 사이드바를 통한 네이버 API Key(Client ID, Client Secret) 입력 및 세션 상태 관리
- 대시보드 사용 가이드 및 소개 페이지 제공
- 각 분석 페이지로 연동하기 위한 설정값 공유
"""

import streamlit as st


def main():
    st.set_page_config(
        page_title="네이버 API 데이터 분석 대시보드",
        page_icon="🚀",
        layout="wide",
    )

    st.title("🚀 네이버 API 데이터 분석 대시보드")
    st.markdown("---")

    from utils.naver_api import render_api_sidebar
    client_id, client_secret = render_api_sidebar()

    # 메인 페이지 가이드
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("💡 대시보드 소개")
        st.markdown(
            """
            이 대시보드는 네이버 오픈 API를 활용하여 다양한 채널의 데이터를 수집하고 시각적으로 분석할 수 있도록 지원합니다.
            
            **제공하는 분석 기능:**
            1. **📈 검색어 트렌드 (Datalab)**: 특정 키워드 그룹의 기간별 상대적 검색 트렌드 분석
            2. **🛍️ 쇼핑 검색**: 검색어별 네이버 쇼핑 상품 최저가 및 브랜드/쇼핑몰 분포 분석
            3. **📝 블로그 검색**: 블로그 포스팅 발행량 및 최신 글 분포 트렌드 분석
            4. **☕ 카페글 검색**: 카페 게시글 트렌드 및 활동성 분석
            5. **📰 뉴스 검색**: 실시간 뉴스 발행 흐름 분석
            6. **📊 쇼핑 트렌드 (Datalab 쇼핑인사이트)**: 카테고리별 쇼핑 클릭 트렌드 비교 분석
            """
        )

        st.subheader("🛠️ 시작하기")
        if not client_id or not client_secret:
            st.warning("⚠️ 왼쪽 사이드바에서 **Naver API Key**를 입력하셔야 대시보드를 사용할 수 있습니다.")
        else:
            st.success("✅ Naver API Key가 설정되었습니다. 왼쪽 메뉴에서 원하시는 분석 페이지를 선택하세요!")

    with col2:
        st.subheader("🔑 API 키 발급 안내")
        st.markdown(
            """
            1. [네이버 개발자 센터](https://developers.naver.com/)에 접속하여 로그인합니다.
            2. **Application > 애플리케이션 등록** 메뉴로 이동합니다.
            3. 애플리케이션 이름 설정 후, 사용 API에서 다음 API들을 추가합니다:
               - **데이터랩(검색어트렌드)**
               - **데이터랩(쇼핑인사이트)**
               - **검색**
            4. 로그인 오픈 API 서비스 환경 설정(웹 설정 등 임의의 URL 입력, 예: `http://localhost`)을 진행합니다.
            5. 등록 완료 후 발급된 **Client ID**와 **Client Secret**을 복사하여 왼쪽 사이드바에 입력합니다.
            """
        )


if __name__ == "__main__":
    main()
