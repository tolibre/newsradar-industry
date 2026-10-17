#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""뉴스레이다 산업부·중기부·개인정보위·대미투자판(서민선 기자용) 생성기.

원본(tolibre/news-monitor — 김광일 기자 출입처판)의 파일을 그대로 가져와
'출입처·바이라인·브라우저 저장키·보관 기간' 같은 설정만 바꿔 이 저장소에 쓴다.
(재경부판 tolibre/newsradar-moef 생성기와 같은 구조 — 설정 블록만 다르다.)

  python tools/make_variant.py <원본 저장소 경로> [<출력 경로, 기본=이 저장소>]

- 치환마다 '원본에서 정확히 몇 번 나와야 하는지'를 적어 두고, 다르면 아무 파일도
  쓰지 않고 멈춘다.
- 원본 쪽 파일은 읽기만 한다. 함수는 바꾸지 않는다(설정·문구만).
- 원본의 주체 출입처 배정·'전체' 탭 주체 가점(+2)·주요 매체 가점(+1)·사진 설명형 제목 거르기는
  원본 값 그대로 쓴다(김광일판과 같음).
"""
import hashlib, os, re, shutil, sys

# ---------------------------------------------------------------- 설정값 ---
REPORTER = "서민선"                       # 노컷 원문 author 메타: 'CBS노컷뉴스 서민선 기자'
BEATS_TITLE = "산업부·중기부·개인정보위·대미투자"
STORE_PREFIX = "nm-ind-"                  # 브라우저 저장키 — 원본('nm-live-')·재경부판('nm-moef-')·국회판('nm-asm-')과
                                          # 같은 출처(tolibre.github.io)라 반드시 달라야 한다
GROUPS = ["산업부", "중기부", "개인정보위", "대미투자"]   # 섹션 순서
REPORT_ORDER_JS = "[" + ",".join(f"'{g}'" for g in GROUPS) + "]"

NEW_BASE_KEYWORDS = '''BASE_KEYWORDS = [
    # 뉴스레이다 산업부·중기부·개인정보위·대미투자판(tools/make_variant.py가 생성 — 직접 고치지 말 것).
    # 그룹명은 원본 당직 모드 매핑(DUTY_KEYWORD_GROUPS)을 그대로 쓴다:
    # 산업통상부·산업부 → '산업부', 중소벤처기업부·중기부 → '중기부', 개인정보보호위원회·개인정보위·개보위 → '개인정보위'.
    # '대미투자'는 기관이 아니라 사안어라 KEYWORD_GROUPS에 넣지 않는다 — 그룹 이름이 곧 '대미투자'가 되고,
    # 클러스터링의 출입처명 토큰·주체 판정 단서에서 빠진다(원본 0-28 '누리호'와 같은 이유).
    "산업통상부", "산업부",
    "중소벤처기업부", "중기부",
    "개인정보보호위원회", "개인정보위", "개보위",
    "대미투자",
]
'''

# 정부 기관장 이름 씨앗 — 이 저장소 DB는 시작 직후라 학습분이 없다. 원본 DB(당직 기간 포함 90일) 제목의
# '기관 + 이름 + 직함' 실측(2026-10-15)으로 채운다. DB 학습이 쌓이면 학습분이 우선한다. 인사가 바뀌면 고칠 것.
SEED = {"김정관": "산업부", "문신학": "산업부", "박정성": "산업부",
        "이소영": "중기부", "이병권": "중기부", "노용석": "중기부",
        "송경희": "개인정보위"}

# (파일, 찾을 문자열 또는 정규식, 바꿀 문자열, 원본에서 나와야 하는 횟수, 정규식 여부)
NM = "news_monitor.py"
RP = "render_page.py"

REPLACEMENTS = [
    # ---- news_monitor.py: 출입처 ----
    # 0-44(2026-10-18): 원본은 당직 출입처 8곳을 날마다 따로 수집한다(알림 없음, 뉴스레이다 '당직' 스위치로만 봄).
    # 산업부판은 쓰지 않는다 — 켜 두면 이 판 출입처에 없는 당직 그룹(국토부·농식품부 등)을 매시간 수집해 DB만 커진다.
    (NM, "DUTY_COLLECT = True\n",
         "DUTY_COLLECT = False   # 산업부판은 당직 수집을 하지 않는다(생성기, 0-44)\n", 1, False),
    (NM, r"BASE_KEYWORDS = \[\n(?:.*\n)*?\]\n", NEW_BASE_KEYWORDS, 1, True),
    (NM, 'TEMP_KEYWORDS = {\n    "대미투자": "2026-09-23",\n}\n',
         "TEMP_KEYWORDS = {}   # 대미투자는 상설 검색어(BASE_KEYWORDS)로 옮겼다\n", 1, False),
    # ---- news_monitor.py: 보관 기간 ----
    # 원본 당직 기간 실측: 산업부·중기부 하루 600~900건씩, 개인정보위 150~370건, 대미투자 400~1,400건(화제 땐 더).
    # 하루 2~3천 건이면 90일치 DB가 GitHub 파일 한도(100MB)에 닿는다(원본 90일 14.8만 건 = 62MB).
    (NM, "RETENTION_DAYS = 90 ", "RETENTION_DAYS = 45 ", 1, False),
    # ---- news_monitor.py: 기관장 이름 씨앗(원본 0-38 자리) ----
    (NM, "ACTOR_PEOPLE_SEED = {}\n", f"ACTOR_PEOPLE_SEED = {SEED!r}   # 산업부판(생성기)\n", 1, False),
    # ---- news_monitor.py: 바이라인(본인 기사 섹션) ----
    (NM, 'BYLINE_NAME = "김광일"', f'BYLINE_NAME = "{REPORTER}"', 1, False),
    (NM, 'BYLINE_SECTION = "김광일 기자"', f'BYLINE_SECTION = "{REPORTER} 기자"', 1, False),

    # ---- render_page.py: 보고 양식 순서 ----
    (RP, "var REPORT_ORDER = ['방미통위','공정위','과기정통부','우주항공청'];",
         f"var REPORT_ORDER = {REPORT_ORDER_JS};", 2, False),
    (RP, "출입처 순서(방미통위 → 공정위 → 과기정통부 → 우주청 → 2진)",
         "출입처 순서(" + " → ".join(GROUPS) + ")", 2, False),
    # ---- render_page.py: 브라우저 저장키(같은 출처의 다른 페이지와 섞이지 않게) ----
    (RP, "'nm-live-", f"'{STORE_PREFIX}", 6, False),
    # ---- render_page.py: 출입처 식별색(원본 네 출입처 색을 차례로) ----
    (RP, '[data-g="공정위"], [data-b="공정위"]', '[data-g="산업부"], [data-b="산업부"]', 1, False),
    (RP, '[data-g="과기정통부"], [data-b="과기정통부"]', '[data-g="중기부"], [data-b="중기부"]', 1, False),
    (RP, '[data-g="방미통위"], [data-b="방미통위"]', '[data-g="개인정보위"], [data-b="개인정보위"]', 1, False),
    (RP, '[data-g="우주항공청"], [data-b="우주항공청"]', '[data-g="대미투자"], [data-b="대미투자"]', 1, False),
    (RP, '[data-g="김광일 기자"], [data-b="김광일 기자"]',
         f'[data-g="{REPORTER} 기자"], [data-b="{REPORTER} 기자"]', 1, False),
    # ---- render_page.py: 기기 연동 숨김(GitHub 계정이 없는 기자는 못 쓴다 — 버튼만 숨김) ----
    (RP, '<button type="button" id="sync" class="sync off"',
         '<button type="button" id="sync" class="sync off" style="display:none"', 1, False),
    # ---- render_page.py: 화면 문구 ----
    (RP, "<title>뉴스레이다</title>", f"<title>뉴스레이다 · {BEATS_TITLE}</title>", 1, False),
    (RP, "document.title = '뉴스레이다 · ' + r.title;",
         "document.title = '뉴스레이다(산업) · ' + r.title;", 1, False),
    (RP, "맨 끝 ‘김광일 기자’는", f"맨 끝 ‘{REPORTER} 기자’는", 1, False),
    (RP, "체크한 기사와 ‘여기까지 확인’은 이 기기에 저장되고, 머리줄 <b>기기 연동</b>을 켜면 다른 기기와 맞춰집니다(내 GitHub 비공개 gist). · <a href=\"../\">최신 다이제스트</a> · <a href=\"../archive/\">지난 다이제스트</a></p>",
         "체크한 기사와 ‘여기까지 확인’은 이 기기(브라우저)에만 저장됩니다 — PC와 폰은 따로 기억합니다.</p>", 1, False),
]

# 원본에서 그대로 가져오는 파일(치환 없음)
COPY_AS_IS = ["merge_db.py", "retitle.py"]

# 페이지에 남아 있으면 안 되는 문자열 — 주석(# / //)이 아닌 줄에서만 검사한다.
# (news_monitor.py는 문자열 대신 아래 EXPECT로 '실제로 import했을 때의 값'을 검사한다.
#  원본의 우주항공청·CBS 매핑·소관 어휘는 남아 있어도 검색어가 아니면 무해하다.)
FORBIDDEN = {
    RP: ["nm-live-", "김광일 기자\"", "기기 연동</b>", "방미통위 → 공정위"],
}
# 생성한 news_monitor.py를 별도 프로세스로 import해 확인할 값(당직·임시 키워드가 꺼진 날짜 기준).
EXPECT = {
    "DUTY_ONLY_GROUPS": [],   # 0-44 — 당직 수집 꺼짐
    "KEYWORDS": ["산업통상부", "산업부", "중소벤처기업부", "중기부", "개인정보보호위원회", "개인정보위", "개보위", "대미투자"],
    "GROUP_ORDER": GROUPS,
    "RETENTION_DAYS": 45,
    "BYLINE_NAME": REPORTER,
    "BYLINE_SECTION": f"{REPORTER} 기자",
    "ACTOR_ASSIGN": True,
    "LIVE_ACTOR_BONUS": 2.0,
    "ACTOR_PEOPLE_SEED": SEED,
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(src_dir):
    out = {}
    for fname in {r[0] for r in REPLACEMENTS}:
        with open(os.path.join(src_dir, fname), encoding="utf-8") as f:
            out[fname] = f.read()
    errors = []
    for fname, old, new, count, is_re in REPLACEMENTS:
        text = out[fname]
        found = len(re.findall(old, text)) if is_re else text.count(old)
        if found != count:
            errors.append(f"{fname}: {old[:60]!r} — {count}번이어야 하는데 {found}번")
            continue
        out[fname] = re.sub(old, lambda m: new, text) if is_re else text.replace(old, new)
    if errors:
        raise SystemExit("원본이 예상과 달라 생성을 멈춥니다(아무 파일도 쓰지 않음):\n  "
                         + "\n  ".join(errors))
    leftovers = []
    for fname, pats in FORBIDDEN.items():
        for i, line in enumerate(out[fname].splitlines(), 1):
            s = line.strip()
            if s.startswith("#") or s.startswith("//"):
                continue
            for p in pats:
                if p in line:
                    leftovers.append(f"{fname}:{i}: {p!r} — {s[:80]}")
    if leftovers:
        raise SystemExit("원본 고유 문자열이 남았습니다:\n  " + "\n  ".join(leftovers))
    return out


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    src = os.path.abspath(sys.argv[1])
    dst = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else
                          os.path.join(os.path.dirname(__file__), ".."))
    out = apply(src)
    # 먼저 임시 폴더에 써서 import 검사를 통과한 뒤에만 실제 위치로 옮긴다.
    import json, subprocess, tempfile
    with tempfile.TemporaryDirectory() as tmp:
        for fname, text in out.items():
            with open(os.path.join(tmp, fname), "w", encoding="utf-8") as f:
                f.write(text)
        probe = ("import json, news_monitor as m; print(json.dumps({k: getattr(m, k) for k in %r}, "
                 "ensure_ascii=False))" % list(EXPECT))
        env = dict(os.environ, DUTY_MODE="")
        r = subprocess.run([sys.executable, "-c", probe], cwd=tmp, env=env,
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("생성본 import 실패:\n" + r.stderr[-2000:])
        got = json.loads(r.stdout.strip().splitlines()[-1])
        bad = {k: (got.get(k), v) for k, v in EXPECT.items() if got.get(k) != v}
        if bad:
            raise SystemExit(f"생성본 설정값이 예상과 다릅니다: {bad}")
    for fname, text in sorted(out.items()):
        with open(os.path.join(dst, fname), "w", encoding="utf-8") as f:
            f.write(text)
    for fname in COPY_AS_IS:
        shutil.copyfile(os.path.join(src, fname), os.path.join(dst, fname))
    for fname in sorted(list(out) + COPY_AS_IS):
        with open(os.path.join(src, fname), "rb") as a, open(os.path.join(dst, fname), "rb") as b:
            print(f"{fname:18s} 원본 {md5(a.read())} → 생성 {md5(b.read())}")


if __name__ == "__main__":
    main()
