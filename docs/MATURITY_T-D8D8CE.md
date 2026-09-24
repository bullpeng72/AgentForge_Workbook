# 성숙도 자기평가 — AgentForge / T-D8D8CE (workbook-complete 이후, 부록 K.5 근거)

본편(《하니스 메서드》)의 5단계 성숙도 모델(L1 임시적 → L2 반복 가능 → L3 팀 조율 →
L4 거버넌스 → L5 조직 확장)에 이 프로젝트를 위치시킨다. 각 항목은 `.aoo/`·`results/`를
직접 열어 확인한 것만 적는다 — 근거 없는 체크는 없다.

## L2 반복 가능 — 충족

- [x] 배치 평가 하네스(`eval/run_batch.py`)
- [x] `agent-eval gate` CI(`.github/workflows/ci.yml`의 quality·gate·team-hygiene 3잡)
- [x] 골든셋 + 버전 비교(`data/golden_examples/v0_cases.json` 4건 → `v2_cases.json` 8건)

## L3 팀 조율 — 부분

- [x] 클레임 로그 — `.aoo/claims.jsonl`에 실제 겹침(c-8e534430 ↔ c-78aa78d9)과 반납·재클레임까지
      남아 있다
- [ ] LiveGuardrail/BranchGuard — 설정된 적 없음(`guardrail_config.json` 자체가 없음).
      SPEC이 애초에 이 범위를 겨냥하지 않았다
- [~] PR 검증 파이프라인 — CI 3잡은 있지만(`ci.yml`), `gh pr list --state all`가 빈 목록을
      반환한다 — 실제 PR 없이 `push` 트리거만 탔다

## L4 거버넌스 — 부분

- [x] RCA + 조치 검증 폐루프 — `.aoo/experiments.jsonl`에 6건 등록, `agent-eval improve
      verify --persist`로 confirmed/refuted 확정
- [ ] SLO를 파일로 고정 — `.aoo/targets.json` 없음(확인함) — `agent-eval target set`을
      실행한 적이 없다
- [x] 스킬 표준화 — `evidence-based-gate-fix`·`background-real-verification`·
      `honest-refuted-experiment-logging` 3종, `skill_merge` 승인 완료
- [x] 2인 승인 — `release_hold`(하윤·수민)·`deploy`(하윤·원우) 둘 다 실전
- [ ] 반려율 자가점검 — `compute_rejection_rate()`를 이 프로젝트에서 호출한 기록이 없다
      (문서·커밋 어디에도 없음, 확인함)
- [ ] 외부/과거 기준 대비 위치 추적 — `.aoo/reference.json` 없음(확인함) — `agent-eval
      benchmark set`을 실행한 적이 없다

## L5 조직 확장 — 미해당

- 팀이 하나(`T-D8D8CE`)뿐 — 여러 팀 공통 기준이나 포트폴리오 단위 승인은 애초에 논의 대상이
  아니다

---

**현재 위치: L3 부분 완성 / L4 초입.** RCA 폐루프와 2인 승인처럼 깊이 들어간 항목이 있는
반면, L4를 완성으로 부르려면 SLO 고정·반려율 자가점검·외부 기준 대비 추적 세 가지가
아직 시도조차 안 됐다는 걸 숨기지 않는다.
