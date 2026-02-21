# Clean Text & Rule Specification v2.0

Owner: 2번 (Cleaner)

------------------------------------------------------------------------

# PART 1. Clean Text Generation Specification

## 1. 목적

`clean_text`는 정책 1건을 임베딩 / RAG / 검색에 사용하기 위한 표준화된
단일 텍스트 표현이다.

목표: - 정책 핵심 정보를 구조적으로 정리 - 노이즈 제거 - LLM 친화적 포맷
유지 - 필드 구조 유지

------------------------------------------------------------------------

## 2. 입력 컬럼 (policies 기준)

사용 컬럼:

-   policy_name (필수)
-   support_summary
-   support_detail
-   eligibility
-   benefit
-   apply_process
-   apply_period
-   raw_text (보조)

------------------------------------------------------------------------

## 3. 결측 처리 규칙

-   "**MISSING**" 같은 토큰 사용 금지
-   None / NaN / "" → 완전 제외
-   값이 없는 섹션은 clean_text에 포함하지 않음

------------------------------------------------------------------------

## 4. 출력 구조 (순서 고정)

\[policy_name\]

\[support_summary\]

\[support_detail\]

\[eligibility\]

\[benefit\]

\[apply_process\]

\[apply_period\]

\[raw\] (최대 2000자)

규칙: - 각 섹션은 \[section_name\] 헤더 사용 - 섹션 사이 빈 줄 1줄 -
존재하는 섹션만 포함 - 전체 길이 최대 6000자

------------------------------------------------------------------------

## 5. 텍스트 정규화

-   `\r\n`{=tex}, `\r →`{=tex} `\n`{=tex}
-   연속 공백 → 1칸
-   줄 단위 strip
-   제어문자 제거

------------------------------------------------------------------------

# PART 2. Rule Parsing Specification

Rule Engine 목적: - 텍스트에서 구조화된 eligibility 조건을 추출 - DB
계약(policy_eligibility)에 맞게 정규화

------------------------------------------------------------------------

## 1. Age Rule (parse_age)

### 인식 패턴

-   만 19세 이상
-   19세 이상
-   만 19\~34세
-   19세 이상 34세 이하

### 출력 구조

constraints 예시: - {"type": "min", "value": 19} - {"type": "max",
"value": 34} - {"type": "range", "min": 19, "max": 34}

### DB 매핑

-   min_age = 최솟값
-   max_age = 최댓값

------------------------------------------------------------------------

## 2. Income Rule (parse_income)

### 인식 패턴

1)  중위소득 비율

-   기준 중위소득 150% 이하
-   중위소득 120% 이상

2)  금액 기준

-   연소득 6,000만원 이하
-   월소득 300만원 이하

3)  분위

-   5분위

------------------------------------------------------------------------

### 내부 constraint.type

-   median_percent_max
-   median_percent_min
-   annual_max_won
-   monthly_max_won
-   decile

------------------------------------------------------------------------

### DB 매핑 규칙

income_rule_type:

-   MEDIAN_RATIO → 중위소득 % 존재 시
-   AMOUNT → 연소득/월소득 존재 시
-   NONE → 조건 없음

income_threshold:

-   annual_max_won → 그대로 사용
-   monthly_max_won → \* 12 후 연소득 기준 변환
-   MEDIAN_RATIO/NONE → null

------------------------------------------------------------------------

## 3. Asset Rule (parse_assets)

### 인식 패턴

-   총자산 3억원 이하
-   재산가액 2억원 이하

### constraint.type

-   max_won

### DB 매핑

-   asset_threshold = 가장 작은 max_won 값
-   없으면 null

------------------------------------------------------------------------

## 4. Vehicle Rule (parse_car)

### 인식 패턴

-   차량가액 2,000만원 이하
-   자동차가액 3천만원 미만

### constraint.type

-   value_max_won

### DB 매핑

-   vehicle_value_limit = 가장 작은 value_max_won
-   없으면 null

------------------------------------------------------------------------

## 5. Homeowner Rule

텍스트에 다음 포함 시 True:

-   무주택
-   주택 미소유
-   자가 없음
-   주택 소유 불가

DB 매핑: - is_homeowner_required = True - 없으면 False

------------------------------------------------------------------------

# PART 3. Contract Alignment

policy_eligibility 필수 조건:

-   income_rule_type ∈ {NONE, AMOUNT, MEDIAN_RATIO}
-   income_threshold는 연소득(원) 기준
-   asset_threshold, vehicle_value_limit 모두 원 단위
-   min_age/max_age nullable 허용

------------------------------------------------------------------------

# PART 4. 설계 철학

1.  계약 우선
2.  DB 적재 가능 구조 유지
3.  확장 가능한 JSON rule 유지
4.  단위 통일 (원, 연소득 기준)
5.  Fail-fast 검증

------------------------------------------------------------------------

End of Specification
