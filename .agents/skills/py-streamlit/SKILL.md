---
name: py-streamlit
description: Streamlit을 사용하여 전문적이고 인터랙티브한 EDA(탐색적 데이터 분석) 대시보드를 구축하는 스킬입니다. 데이터 개요, 단일/이변량/다변량 분석, 결측치/이상치 탐지, 그리고 동적 필터링 기능을 포함한 고성능 웹 앱을 제작할 때 사용하세요. 사용자가 "Streamlit EDA", "데이터 대시보드", "인터랙티브 시각화 앱" 등을 언급할 때 반드시 이 스킬을 호출하십시오.
---

# py-streamlit 스킬 가이드

이 스킬은 사용자가 제공한 데이터를 기반으로 Streamlit을 활용해 30가지 핵심 EDA 기능을 갖춘 대시보드를 구축하도록 돕습니다.

## 1. 대시보드 기본 구조 (Layout)
- **사이드바(Sidebar):** 데이터 로드 버튼, 글로벌 필터, 분석 페이지 선택 메뉴를 배치합니다.
- **메인 페이지:** 탭(Tabs) 또는 확장기(Expander)를 사용하여 분석 단계를 구분합니다.
  - 예: `tab1, tab2, tab3 = st.tabs(["데이터 개요", "변수별 분석", "관계 분석"])`
- **캐싱:** 데이터 로딩 및 무거운 연산은 `@st.cache_data`를 사용하여 성능을 최적화합니다.

## 2. 30가지 핵심 기능 구현 지침

### 📊 1. 데이터 개요 및 프로파일링
1. **기본 정보:** `st.metric`을 사용하여 행/열 수, 메모리 사용량을 표시합니다.
2. **타입 관리:** `df.dtypes`를 보여주고 `st.multiselect` 등으로 타입을 강제 변경하는 UI를 제공합니다.
3. **요약 통계:** `df.describe()` 결과를 깔끔한 표로 제시합니다.
4. **고유값 분석:** 컬럼별 `nunique()` 및 비율을 계산하여 표시합니다.
5. **데이터 뷰어:** `st.dataframe`을 사용하며, 상단/하단/샘플링 선택 기능을 넣습니다.

### 📈 2. 단일 변수 분석 (Univariate)
6. **연속 분포:** Plotly의 `histogram`과 KDE를 활용합니다.
7. **비대칭 지표:** `scipy.stats.skew`, `kurtosis` 값을 수치로 제공합니다.
8. **범주형 분석:** `plotly.express.bar` 또는 `pie` 차트로 비율을 시각화합니다.
9. **희소 범주:** 빈도가 임계값(예: 1% 미만) 이하인 값을 리스트업합니다.
10. **시계열 분포:** 날짜형 컬럼의 히스토그램으로 데이터 집중도를 확인합니다.

### 🔍 3. 결측치 및 이상치 분석
11. **결측치 수치화:** 컬럼별 결측수와 %를 표로 보여줍니다.
12. **패턴 시각화:** 결측치 상관계수 히트맵 또는 Bar 차트를 구현합니다.
13. **이상치 시각화:** `st.plotly_chart`로 Boxplot 또는 Violin plot을 생성합니다.
14. **탐지 로직:** IQR(1.5*IQR) 기반으로 이상치 행을 필터링하여 보여줍니다.
15. **정제 시뮬레이션:** 결측치 대체 전/후의 분포 변화를 나란히 비교합니다.

### ⚖️ 4. 이변량 분석 (Bivariate)
16. **산점도:** `px.scatter`에 `trendline="ols"`를 추가하여 방향성을 보여줍니다.
17. **그룹 비교:** 범주형(X) vs 수치형(Y) Boxplot으로 그룹 간 차이를 비교합니다.
18. **교차표:** `pd.crosstab` 결과와 Heatmap을 함께 제시합니다.
19. **시계열 추이:** `px.line`으로 시간에 따른 수치 변화를 분석합니다.
20. **그룹 요약:** `df.groupby().agg()` 결과를 인터랙티브한 표로 제공합니다.

### 🕸️ 5. 다변량 분석 (Multivariate)
21. **상관 히트맵:** `df.corr()` 결과를 Plotly Heatmap으로 시각화합니다.
22. **다차원 매핑:** 산점도에서 `color`, `size`, `symbol` 인자에 변수를 할당합니다.
23. **페어플롯:** 선택한 변수들에 대해 `px.scatter_matrix`를 생성합니다.
24. **타겟 연관성:** 타겟 변수와 다른 변수들 간의 상관계수 순위를 차트로 보여줍니다.
25. **다중 시리즈:** 하나의 시간축에 여러 Y축 변수를 겹쳐서 비교합니다.

### 🎛️ 6. 동적 제어 및 UX
26. **글로벌 필터:** 사이드바 필터 변경 시 `st.session_state` 또는 리턴값을 통해 모든 차트가 업데이트되게 합니다.
27. **동적 변수 선택:** 차트의 X, Y, Color 변수를 `st.selectbox`로 선택 가능하게 만듭니다.
28. **세부 컨트롤:** Bins 조절(`st.slider`), Log Scale(`st.checkbox`) 옵션을 제공합니다.
29. **인터랙티브 탐색:** Plotly의 툴팁, 줌, 범례 필터 기능을 기본으로 활용합니다.
30. **내보내기:** `st.download_button`을 사용하여 결과 데이터(CSV)나 리포트를 다운로드 가능하게 합니다.

## 3. 권장 기술 스택
- **Base:** Streamlit
- **Data:** Pandas, NumPy, Scipy
- **Viz:** Plotly (인터랙티브 기능 필수), Altair (선택)
- **Stats:** Scipy.stats

## 4. 예시 코드 패턴
```python
import streamlit as st
import pandas as pd
import plotly.express as px

# 데이터 로딩
@st.cache_data
def load_data(file):
    return pd.read_csv(file)

def main():
    st.set_page_config(layout="wide")
    st.title("🚀 Professional EDA Dashboard")
    
    # 1. 사이드바 - 파일 업로드 및 필터링
    # 2. 탭 구성
    # 3. 30가지 기능 순차 구현
    
if __name__ == "__main__":
    main()
```

