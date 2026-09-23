from __future__ import annotations

from agent_evaluator import PerformanceMonitor, agent_eval
from agent_evaluator.decorators import EvalMetadata

from agentforge.pipeline import run as _run_pipeline

monitor = PerformanceMonitor(output_dir="results/", agent_version="auto")


@agent_eval(monitor, task_type="planning", question_arg="brief")
def run(brief: str) -> tuple[str, EvalMetadata]:
    """AgentForge 파이프라인 자체를 최초로 계측한다(Part VI 착수 — 이전엔 계측 없음).

    Gate A-G 전부를 겨냥한 Config 배선은 Part VII(Gate 정면돌파)에서 한다 — 지금은
    completion_score(검증 통과 여부)와 결과 메타데이터만 기록해 결과 파일이 쌓이게 한다.
    """
    result = _run_pipeline(brief)
    response = f"domain={result.golden_data.domain} roles={result.team_design.roles}"
    metadata = EvalMetadata(
        completion_score=1.0 if result.verification.passed else 0.0,
        errors=result.verification.errors or None,
        extra={
            "domain": result.golden_data.domain,
            "roles": result.team_design.roles,
            "verification_passed": result.verification.passed,
        },
    )
    return response, metadata
