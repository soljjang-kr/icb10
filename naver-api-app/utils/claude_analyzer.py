"""
Claude AI를 활용한 네이버 API 수집 데이터 분석 유틸리티입니다.

주요 기능:
- Anthropic SDK를 사용하여 Claude AI API에 연결
- 수집된 데이터를 Claude에게 전달하여 AI 인사이트 생성
- 검색 트렌드, 쇼핑, 블로그, 뉴스, 카페 데이터 분석 지원
- 프롬프트 캐싱을 통한 비용 최적화

주의사항:
- ANTHROPIC_API_KEY 또는 사용자 입력 API 키 필요
- 모델: claude-sonnet-4-6 (비용 효율적인 분석용)
"""

import anthropic
import json
import pandas as pd


# 분석에 사용할 Claude 모델
CLAUDE_MODEL = "claude-sonnet-4-6"

# 공통 시스템 프롬프트 (프롬프트 캐싱 적용)
SYSTEM_PROMPT = """당신은 한국 시장의 데이터 분석 전문가입니다.
네이버 API를 통해 수집된 검색 트렌드, 쇼핑, 블로그, 뉴스, 카페 데이터를 분석하여
마케터와 비즈니스 관계자에게 유용한 인사이트를 제공합니다.

분석 시 다음 원칙을 따릅니다:
1. 데이터에 근거한 객관적 분석
2. 실무에 바로 활용 가능한 구체적 제안
3. 한국 시장의 맥락과 트렌드 고려
4. 마크다운 형식으로 가독성 높게 작성
5. 핵심 인사이트를 먼저 제시하고 상세 분석은 후술"""


def analyze_trend_data(api_key: str, data: dict, keywords: list) -> str:
    """
    검색어 트렌드 데이터를 Claude AI로 분석합니다.

    Args:
        api_key: Claude API 키
        data: 네이버 데이터랩 API 응답 데이터
        keywords: 분석 대상 검색어 목록

    Returns:
        Claude AI 분석 결과 텍스트
    """
    client = anthropic.Anthropic(api_key=api_key)

    # 데이터 요약 생성
    results_summary = []
    if "results" in data:
        for result in data["results"]:
            group_name = result.get("title", "")
            values = result.get("data", [])
            if values:
                avg_ratio = sum(v.get("ratio", 0) for v in values) / len(values)
                max_ratio = max(v.get("ratio", 0) for v in values)
                min_ratio = min(v.get("ratio", 0) for v in values)
                results_summary.append(
                    f"- {group_name}: 평균 {avg_ratio:.1f}, 최대 {max_ratio:.1f}, 최소 {min_ratio:.1f}"
                )

    prompt = f"""다음은 네이버 데이터랩에서 수집한 검색어 트렌드 데이터입니다.

**분석 대상 키워드:** {', '.join(keywords)}

**트렌드 수치 요약:**
{chr(10).join(results_summary)}

**전체 데이터:**
```json
{json.dumps(data, ensure_ascii=False, indent=2)[:3000]}
```

위 데이터를 분석하여 다음 항목을 제공해 주세요:
1. **📊 핵심 트렌드 요약**: 가장 눈에 띄는 트렌드 패턴
2. **📈 성장/하락 키워드 분석**: 기간 중 주목할 변화
3. **🕐 시기별 특이점**: 급상승·급하락 시점과 가능한 원인
4. **💡 마케팅 제안**: 트렌드를 활용한 실무 제안
5. **⚠️ 주의사항**: 데이터 해석 시 고려할 점"""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except anthropic.AuthenticationError:
        return "❌ Claude API 키가 올바르지 않습니다. 사이드바에서 API 키를 확인해 주세요."
    except anthropic.APIStatusError as e:
        return f"❌ Claude API 오류: {e.message}"
    except Exception as e:
        return f"❌ 분석 중 오류가 발생했습니다: {str(e)}"


def analyze_search_results(api_key: str, df: pd.DataFrame, query: str, api_type: str) -> str:
    """
    검색 결과 데이터(블로그/뉴스/카페/쇼핑)를 Claude AI로 분석합니다.

    Args:
        api_key: Claude API 키
        df: 검색 결과 데이터프레임
        query: 검색어
        api_type: API 유형 ('blog' | 'news' | 'cafearticle' | 'shop')

    Returns:
        Claude AI 분석 결과 텍스트
    """
    client = anthropic.Anthropic(api_key=api_key)

    # API 유형별 한글 이름 매핑
    type_names = {
        "blog": "블로그",
        "news": "뉴스",
        "cafearticle": "카페",
        "shop": "쇼핑",
    }
    type_name = type_names.get(api_type, api_type)

    # 데이터 요약
    total_count = len(df)
    data_preview = df.head(20).to_string(index=False) if not df.empty else "데이터 없음"

    # 쇼핑의 경우 가격 통계 추가
    price_stats = ""
    if api_type == "shop" and "lprice" in df.columns:
        try:
            df_price = df.copy()
            df_price["lprice"] = pd.to_numeric(df_price["lprice"], errors="coerce")
            price_stats = f"""
**가격 통계:**
- 평균 최저가: {df_price['lprice'].mean():,.0f}원
- 최저가: {df_price['lprice'].min():,.0f}원
- 최고가: {df_price['lprice'].max():,.0f}원
"""
        except Exception:
            pass

    prompt = f"""다음은 네이버 {type_name} 검색 결과 데이터입니다.

**검색어:** {query}
**수집 건수:** {total_count}건
{price_stats}

**상위 20건 미리보기:**
```
{data_preview[:3000]}
```

위 데이터를 분석하여 다음 항목을 제공해 주세요:
1. **📌 콘텐츠 특징 분석**: 수집된 {type_name} 콘텐츠의 주요 특징
2. **🔥 주목할 만한 내용**: 가장 눈에 띄는 항목이나 패턴
3. **📊 데이터 인사이트**: 수치 및 패턴에서 도출되는 인사이트
4. **💡 활용 제안**: 수집 데이터를 비즈니스에 활용하는 방법
5. **🔍 추가 분석 권장사항**: 더 깊은 분석을 위한 제안"""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except anthropic.AuthenticationError:
        return "❌ Claude API 키가 올바르지 않습니다. 사이드바에서 API 키를 확인해 주세요."
    except anthropic.APIStatusError as e:
        return f"❌ Claude API 오류: {e.message}"
    except Exception as e:
        return f"❌ 분석 중 오류가 발생했습니다: {str(e)}"


def analyze_shopping_trend(api_key: str, data: dict, categories: list) -> str:
    """
    쇼핑인사이트 트렌드 데이터를 Claude AI로 분석합니다.

    Args:
        api_key: Claude API 키
        data: 네이버 데이터랩 쇼핑인사이트 API 응답
        categories: 분석 카테고리 목록

    Returns:
        Claude AI 분석 결과 텍스트
    """
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""다음은 네이버 데이터랩 쇼핑인사이트에서 수집한 카테고리 트렌드 데이터입니다.

**분석 카테고리:** {', '.join(categories)}

**수집 데이터:**
```json
{json.dumps(data, ensure_ascii=False, indent=2)[:3000]}
```

위 쇼핑 트렌드 데이터를 분석하여 다음 항목을 제공해 주세요:
1. **🛍️ 쇼핑 트렌드 요약**: 카테고리별 쇼핑 관심도 변화
2. **📈 성장 카테고리**: 성장세가 두드러진 쇼핑 카테고리
3. **📉 하락 카테고리**: 관심도가 낮아진 카테고리
4. **🕐 계절성 분석**: 시기별 쇼핑 패턴 특이점
5. **💡 셀러/마케터 제안**: 쇼핑 트렌드를 활용한 전략 제안"""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except anthropic.AuthenticationError:
        return "❌ Claude API 키가 올바르지 않습니다. 사이드바에서 API 키를 확인해 주세요."
    except anthropic.APIStatusError as e:
        return f"❌ Claude API 오류: {e.message}"
    except Exception as e:
        return f"❌ 분석 중 오류가 발생했습니다: {str(e)}"
