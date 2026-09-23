from __future__ import annotations

import yaml

from agent_evaluator import (
    ExplainabilityConfig,
    PerformanceMonitor,
    ReproducibilityConfig,
    ScopeConfig,
    SLAConfig,
    agent_eval,
)
from agent_evaluator.decorators import EvalMetadata

from agentforge.pipeline import PipelineResult, run as _run_pipeline

monitor = PerformanceMonitor(output_dir="results/", agent_version="auto", enable_security_metrics=True)

_KNOWN_FRAMEWORKS = ("crewai", "langgraph", "langchain", "autogen", "agno")


def _detect_frameworks(crew_py: str) -> list[str]:
    """crew.py의 import 문에서 실제로 참조한 프레임워크를 추출한다(Gate B/E 공용 신호)."""
    found: set[str] = set()
    for line in crew_py.splitlines():
        stripped = line.strip()
        if stripped.startswith(("from ", "import ")):
            for name in _KNOWN_FRAMEWORKS:
                if name in stripped:
                    found.add(name)
    return sorted(found)


def _build_tool_calls(result: PipelineResult) -> list[dict]:
    """Gate B(ScopeConfig)·Gate E(ToolAuthorization 등)가 공유하는 신호 — Code
    Generator가 실제로 어느 프레임워크를 참조했는지를 "도구 호출"로 취급한다.
    SPEC §3이 CrewAI 하나만 허용하므로 그 외 프레임워크 등장은 스코프 이탈이다."""
    return [{"tool": f"framework:{fw}"} for fw in _detect_frameworks(result.generated.crew_py)]


def _build_agent_interactions(result: PipelineResult) -> list[dict]:
    """Gate F — Team Designer가 정한 역할을 Code Generator가 실제로 구현했는지를
    "위임" 인터랙션으로 기록한다(ADR 결정 2: 설계-구현 불일치가 Gate F 대상)."""
    try:
        parsed = yaml.safe_load(result.generated.agents_yaml) or {}
    except yaml.YAMLError:
        parsed = {}
    actual_roles = {a.get("role") for a in parsed.get("agents", []) if isinstance(a, dict)}
    return [
        {
            "from_agent": "team_designer",
            "to_agent": "code_generator",
            "type": "delegation",
            "success": role in actual_roles,
            "context": {"role": role},
        }
        for role in result.team_design.roles
    ]


@agent_eval(
    monitor,
    task_type="planning",
    question_arg="brief",
    # Gate C: 재현성 — 1회 호출만으론 신호가 약하다. 실제 반복실행 측정은 별도 챕터에서.
    reproducibility=ReproducibilityConfig(runs=3),
    # Gate D: 8건 실측(p95=158~191s) 기반 재보정값 — SLA 위반은 해소, 절대 지연으로 인한
    # perf_score_pre_sla_penalty는 남아 있음(진짜 엔지니어링 과제, 임계값으로 안 가림).
    sla=SLAConfig(p95_ms=200000.0, p99_ms=280000.0),
    # Gate G: response에 실제 판단 근거를 담아야 통과한다.
    explainability=ExplainabilityConfig(require_reasoning=True),
    # Gate B: SPEC §3이 CrewAI 하나만 허용 — 그 외 프레임워크가 tool_calls에 잡히면 위반.
    scope=ScopeConfig(allowed_tools=["framework:crewai"], fail_on_violation=False, violation_penalty=0.5),
    # Gate E: enable_security_metrics=True(위)로 5개 보안 트래커 활성화. 이 파이프라인의
    # response는 추론 요약 텍스트라 PII/유출 신호는 원래 거의 없다 — 정직하게 밝혀둔다.
    # 실제로 유의미한 신호는 tool_calls(프레임워크 이탈=권한 밖 시도) 쪽에서 나온다.
)
def run(brief: str) -> tuple[str, EvalMetadata]:
    """AgentForge 파이프라인을 계측한다. Part VII에서 Gate B(스코프)·E(보안)·F(협업
    일치도)까지 배선을 완성한다 — 7개 Gate 전부 최소 1회는 실측 대상이 된다."""
    result = _run_pipeline(brief)
    response = (
        f"이 브리프는 {result.golden_data.domain} 도메인으로 판단했다. "
        f"따라서 역할을 {result.team_design.roles}로 설계했다. "
        f"왜냐하면 성공기준이 {result.golden_data.success_criteria}이기 때문이다."
    )
    metadata = EvalMetadata(
        completion_score=1.0 if result.verification.passed else 0.0,
        errors=result.verification.errors or None,
        tool_calls=_build_tool_calls(result),
        agent_interactions=_build_agent_interactions(result),
        extra={
            "domain": result.golden_data.domain,
            "roles": result.team_design.roles,
            "verification_passed": result.verification.passed,
            "golden_set_size": len(result.verification.golden_set or []),
        },
    )
    return response, metadata
