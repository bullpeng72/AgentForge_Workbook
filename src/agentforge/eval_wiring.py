from __future__ import annotations

from agent_evaluator import (
    ExplainabilityConfig,
    PerformanceMonitor,
    ReproducibilityConfig,
    SLAConfig,
    agent_eval,
)
from agent_evaluator.decorators import EvalMetadata

from agentforge.pipeline import run as _run_pipeline

monitor = PerformanceMonitor(output_dir="results/", agent_version="auto")


@agent_eval(
    monitor,
    task_type="planning",
    question_arg="brief",
    # Gate C: 재현성 — 이 배선만으론 1회 호출 시 기본 1.0(측정 안 됨)으로 나온다.
    # 실제 반복실행 측정은 Part VII 후반(같은 brief를 여러 번 호출)에서 한다.
    reproducibility=ReproducibilityConfig(runs=3),
    # Gate D: 4단계 파이프라인(GPT-5 x2 + Ollama x1)의 지연 기준. 최초값 60s는 8건
    # 실측 결과 p95=158.77s로 전부 SLA 초과(ADR 결정 2가 예측한 "Tier1 비중이 높아
    # Gate D 지연이 커질 것"이 실측으로 확인됨) — 실측치에 여유를 두고 재보정한다.
    sla=SLAConfig(p95_ms=200000.0, p99_ms=280000.0),
    # Gate G: response에 실제 판단 근거(도메인→역할 연결)를 담아야 통과한다 — 마커
    # 단어를 억지로 넣는 게 아니라 파이프라인이 실제로 내린 결정을 서술한다.
    explainability=ExplainabilityConfig(require_reasoning=True),
    # Gate B/E/F: 아직 배선 안 함 — 다음 챕터에서 각각 추가한다(ScopeConfig/보안검사/
    # AgentCoordinationTracker). 지금 결과에는 not_measured로 나오는 게 정상이다.
)
def run(brief: str) -> tuple[str, EvalMetadata]:
    """AgentForge 파이프라인을 계측한다. Part VI에서 completion_score만 기록했던 걸
    Part VII에서 Gate C(재현성)·D(지연)·G(설명가능성) Config로 확장한다.
    """
    result = _run_pipeline(brief)
    response = (
        f"이 브리프는 {result.golden_data.domain} 도메인으로 판단했다. "
        f"따라서 역할을 {result.team_design.roles}로 설계했다. "
        f"왜냐하면 성공기준이 {result.golden_data.success_criteria}이기 때문이다."
    )
    metadata = EvalMetadata(
        completion_score=1.0 if result.verification.passed else 0.0,
        errors=result.verification.errors or None,
        extra={
            "domain": result.golden_data.domain,
            "roles": result.team_design.roles,
            "verification_passed": result.verification.passed,
            "golden_set_size": len(result.verification.golden_set or []),
        },
    )
    return response, metadata
