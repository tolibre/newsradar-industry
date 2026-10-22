# 뉴스레이다 · 산업부·중기부·개인정보위·대미투자판

CBS노컷뉴스 서민선 기자용 보고 준비 페이지.
원본 [tolibre/news-monitor](https://github.com/tolibre/news-monitor)(김광일 기자 출입처판)에서 설정만 바꿔 만든 판이다.
같은 방식: 재경부판 [tolibre/newsradar-moef](https://github.com/tolibre/newsradar-moef) · 국회판 [tolibre/newsradar-assembly](https://github.com/tolibre/newsradar-assembly).

- 페이지: https://tolibre.github.io/newsradar-industry/ (→ `/live/`)
- 섹션: 산업부 · 중기부 · 개인정보위 · 대미투자 (+ 맨 끝 서민선 기자 본인 기사, 보고 양식에서 `<기처리>`)
- 보고: 업무일 09:00 · 14:00 (원본과 같은 구간·화면 전환 시각)

## 코드를 직접 고치지 말 것

`news_monitor.py`·`render_page.py`·`merge_db.py`·`retitle.py`는 **`tools/make_variant.py`가 원본에서 생성**한다.

```
git clone --depth 1 https://github.com/tolibre/news-monitor /tmp/nm
python tools/make_variant.py /tmp/nm .
```

생성기는 치환마다 원본 등장 횟수를 검사하고, 생성본을 import해 검색어·그룹·보관 기간 값을 확인한 뒤에만 파일을 쓴다. 함수는 바꾸지 않는다.

## 원본과 다른 점

| | 원본 | 이 판 |
|---|---|---|
| 검색어 | 공정위·방미통위·과기정통부·우주항공청·CBS 등 | 산업통상부·산업부 · 중소벤처기업부·중기부 · 개인정보보호위원회·개인정보위·개보위 · 대미투자 |
| 그룹 | — | 원본 당직 매핑 그대로(산업부·중기부·개인정보위). '대미투자'는 사안어라 매핑하지 않음(클러스터링 출입처명 토큰·주체 판정 단서에서 빠짐) |
| 휴일 특근(당직) | 경제정책팀 8곳(김광일 출입처 제외) | **경제정책팀 묶음**(김승모·김광일·서민선·이승훈·최창민 다섯 명 출입처 합침, `tools/econ_team.py`) 중 이 판 섹션이 아닌 것 — '휴일 특근' 스위치로 봄(0-73). 원본 공정위 오탐 제외어(대한체육회 등)는 그대로 |
| DB 보관 | 90일 | 45일 (하루 2~3천 건 예상 — 90일이면 GitHub 파일 한도 100MB에 닿음) |
| 기관장 이름 씨앗 | — | 김정관·문신학·박정성(산업부), 이소영·이병권·노용석(중기부), 송경희(개인정보위) — DB 학습이 쌓이면 학습분 우선 |
| 본인 기사 섹션 | 김광일 기자 | 서민선 기자 |
| 브라우저 저장키 | `nm-live-*` | `nm-ind-*` |
| 기기 연동·텔레그램·digest 페이지·수확 | 있음 | 없음(재경부판과 같음) |

주체 출입처 배정·'전체' 탭 주체 가점·주요 매체 가점·사진 설명형 제목 거르기는 원본(김광일판)과 같다.

## 운영 (cron-job.org → workflow_dispatch)

URL `https://api.github.com/repos/tolibre/newsradar-industry/actions/workflows/newsradar-industry.yml/dispatches`, POST,
헤더는 원본 잡과 같음(PAT `news-monitor-cron`에 이 저장소 추가 필요), 시간대 Asia/Seoul.

| 잡 | 스케줄 | body |
|---|---|---|
| ind-check | `0 5-22 * * *` | `{"ref":"main","inputs":{"mode":"check"}}` |
| ind-precut | `25 8,13 * * 1-5` | 위와 같음 |
| ind-digest | `0 6 * * *` | `{"ref":"main","inputs":{"mode":"digest"}}` |
| ind-retitle | `15 */2 * * *` | `{"ref":"main","inputs":{"mode":"retitle","apply":"1","limit":"100"}}` |

Secrets: `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`(원본과 같은 값). Pages: main / docs.
