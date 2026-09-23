# deploy — AgentForge (T-D8D8CE)

## 배경

`release_hold`(phase 6→7, `release-hold-approved` 태그) 승인 완료 — 전체 리스크 명세는
`docs/RELEASE_HOLD_T-D8D8CE.md` 참고, 요약은 반복하지 않는다.

## 이 저장소에서 "배포"가 뜻하는 것

이 프로젝트는 상용 SDK가 아니라 《AgentForge 실습서》의 동봉 예제 저장소다 — PyPI 배포나
프로덕션 인프라 전개가 없다(SPEC §3 Out-of-scope). "deploy"는 이 저장소를 **책의 최종
동봉본으로 확정**한다는 뜻이다: main 브랜치가 v0-v5 전체를 담고 있고, README·SPEC·ADR·
LIMITS가 실제 상태와 일치하며, CI가 green이고, 독자가 그대로 따라 할 수 있는 상태.

## 배포 전 최종 확인

- [x] `pytest tests/unit/` 51/51 통과 (오프라인, LLM 호출 없음)
- [x] CI 3잡(`quality`·`gate`·`team-hygiene`) green — `team-ci-ready` 태그 시점 확인,
      이후 커밋도 동일 워크플로 유지(변경 없음)
- [x] `.env`가 매 커밋마다 `git status`/`git check-ignore`로 검증됨 — 실 API 키 유출 없음
- [x] README가 실제 상태(v0-v5, 마일스톤 태그, 알려진 갭)를 반영하도록 갱신됨
- [x] `release_hold` 2인 승인 완료(하윤·수민)

## 결정

`release_hold`에서 명시한 갭(Gate D/F warn, v4 골든셋 커버리지 없음)을 안고 그대로
배포한다 — 이 저장소의 가치는 "완벽한 시스템"이 아니라 "Harness Gate 마찰을 실제로
겪고 정직하게 기록한 과정"이다.
