# parser.py
# ------------------------------------------------------------
# 역할
# 1) URL 기반으로 source 자동 판별
# 2) URL에 포함된 고유키 기반으로 policy_id 생성
#    - 서울주거포털: /content/sh01_061030 -> sh01_061030
#    - 복지로: ?wlfareInfoId=WLF00006181 -> bokjiro_WLF00006181
# 3) canonical link 정규화
# 4) HTML -> raw_text(텍스트 원문) 추출 + 섹션(best-effort) 추출
# ------------------------------------------------------------

from __future__ import annotations

import re
import time
import hashlib
from dataclasses import dataclass
from typing import Dict, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import requests
from bs4 import BeautifulSoup


@dataclass
class ParsedPolicy:
    policy_id: str
    source: str
    canonical_link: str

    raw_text: str

    eligibility: str = ""
    benefit: str = ""
    apply_process: str = ""
    apply_period: str = ""


# -----------------------------
# 공용 유틸
# -----------------------------
def normalize_whitespace(text: str) -> str:
    """공백/개행 정리 (raw_text 품질 + 해시 안정화 목적)"""
    if not text:
        return ""
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def detect_source(url: str) -> str:
    """링크 도메인 기준 source 분류"""
    host = (urlparse(url).netloc or "").lower()
    if "housing.seoul.go.kr" in host:
        return "seoul_housing_portal"
    if "bokjiro.go.kr" in host:
        return "bokjiro"
    return "unknown"


def build_fallback_policy_id(url: str, policy_name: str = "") -> str:
    """
    URL에 고유키가 없는 경우만 사용하는 fallback ID
    - canonical_url + policy_name을 합쳐 sha1 -> p_<hex>
    """
    base = (url or "") + "||" + (policy_name or "")
    h = hashlib.sha1(base.encode("utf-8")).hexdigest()
    return f"p_{h[:16]}"


def extract_policy_id_and_canonical(url: str, policy_name: str = "") -> Tuple[str, str, str]:
    """
    URL에서 (policy_id, canonical_link, source)를 추출.
    - 고유키가 보이면 무조건 그걸 policy_id로 사용 (가장 안정적)
    - 고유키가 없을 때만 fallback(p_해시)
    """
    p = urlparse(url)
    host = (p.netloc or "").lower()
    path = p.path or ""
    qs = parse_qs(p.query)

    source = detect_source(url)

    # 1) 복지로: wlfareInfoId가 고유키
    if "bokjiro.go.kr" in host:
        wlfare_id = (qs.get("wlfareInfoId", [None])[0] or "").strip()
        if wlfare_id:
            policy_id = f"bokjiro_{wlfare_id}"
            # canonical: wlfareInfoId만 유지
            canonical_query = urlencode({"wlfareInfoId": wlfare_id})
            canonical = urlunparse((
                p.scheme or "https",
                p.netloc,
                p.path,
                "",
                canonical_query,
                ""
            ))
            return policy_id, canonical, source

    # 2) 서울주거포털: /content/sh01_061030 형태 (숫자 길이 가정 X)
    if "housing.seoul.go.kr" in host:
        # /content/sh01_061030 처럼 마지막 세그먼트에서 추출
        m = re.search(r"/content/(sh\d{2}_[0-9]+)", path)
        if m:
            policy_id = m.group(1)
            canonical = f"{p.scheme or 'https'}://{p.netloc}/site/main/content/{policy_id}"
            return policy_id, canonical, source

    # 3) 기타/unknown: canonical을 원본으로 두고 fallback ID 생성
    canonical = url
    policy_id = build_fallback_policy_id(canonical, policy_name=policy_name)
    return policy_id, canonical, source


def fetch_html(url: str, timeout: int = 25, max_retries: int = 3,
              min_sleep: float = 0.8, max_sleep: float = 1.6) -> str:
    """HTML 수집 (간단 재시도 포함)"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PolicyCrawler/1.0"
    }

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            last_err = e
            # 재시도 텀
            if attempt < max_retries:
                sleep_s = min_sleep + (max_sleep - min_sleep) * (attempt - 1) / max(1, (max_retries - 1))
                time.sleep(sleep_s)

    raise RuntimeError(f"Failed to fetch HTML: {url} / last_err={last_err}")


def html_to_raw_text(html: str) -> str:
    """HTML -> 화면 텍스트(best-effort)"""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n")
    return normalize_whitespace(text)


# -----------------------------
# 섹션(best-effort) 추출
# -----------------------------
SECTION_ALIASES: Dict[str, Tuple[str, ...]] = {
    "eligibility": ("지원대상", "대상", "자격", "신청자격", "선정기준", "지원 자격"),
    "benefit": ("지원내용", "혜택", "지원 혜택", "지원금", "지원금액", "급여내용", "서비스내용"),
    "apply_process": ("신청방법", "신청", "접수방법", "이용방법", "신청 절차", "절차"),
    "apply_period": ("신청기간", "기간", "접수기간", "모집기간", "신청 시기", "신청 시점"),
}


def extract_sections_from_raw_text(raw_text: str) -> Dict[str, str]:
    """
    raw_text에서 섹션 헤더 단어를 기준으로 best-effort로 잘라내기.
    - 사이트 구조가 달라도 최소한의 구조화 필드를 만들기 위한 방법
    """
    out = {"eligibility": "", "benefit": "", "apply_process": "", "apply_period": ""}
    if not raw_text:
        return out

    lines = [ln.strip() for ln in raw_text.split("\n") if ln.strip()]
    if not lines:
        return out

    hits = []  # (line_index, key)
    for i, ln in enumerate(lines):
        compact = re.sub(r"[\[\]\(\)\-:：·•\s]", "", ln)
        for key, aliases in SECTION_ALIASES.items():
            for alias in aliases:
                alias_compact = re.sub(r"[\[\]\(\)\-:：·•\s]", "", alias)
                if compact == alias_compact:
                    hits.append((i, key))
                    break

    if not hits:
        return out

    hits.sort(key=lambda x: x[0])
    for idx, (start_i, key) in enumerate(hits):
        end_i = hits[idx + 1][0] if idx + 1 < len(hits) else len(lines)
        body = "\n".join(lines[start_i + 1:end_i])
        out[key] = normalize_whitespace(body)

    return out


def parse_policy_page(url: str, policy_name: str = "",
                      max_retries: int = 3, min_sleep: float = 0.8, max_sleep: float = 1.6) -> ParsedPolicy:
    """
    정책 페이지 1개 파싱:
    - policy_id/source/canonical 결정
    - HTML 수집 -> raw_text 추출
    - 섹션 best-effort 추출
    """
    policy_id, canonical, source = extract_policy_id_and_canonical(url, policy_name=policy_name)

    html = fetch_html(url, max_retries=max_retries, min_sleep=min_sleep, max_sleep=max_sleep)
    raw_text = html_to_raw_text(html)
    sections = extract_sections_from_raw_text(raw_text)

    return ParsedPolicy(
        policy_id=policy_id,
        source=source,
        canonical_link=canonical,
        raw_text=raw_text,
        eligibility=sections.get("eligibility", ""),
        benefit=sections.get("benefit", ""),
        apply_process=sections.get("apply_process", ""),
        apply_period=sections.get("apply_period", ""),
    )
