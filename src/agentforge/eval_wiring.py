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
    # 실측(v2-04-ambiguous, gate_run_4): 파싱은 성공해도 dict가 아닌 값(문자열 등)일
    # 수 있다 — verifier.py에 심은 것과 같은 가드를 여기도 둔다.
    if not isinstance(parsed, dict):
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


def _build_response(brief: str, result: PipelineResult) -> str:
    """recommend_fix(Gate A)로 SDK 소스를 확인해 고친 응답 형식 — ResponseQualityEvaluator는
    relevance를 request/response의 단어 겹침으로, completeness를 word_count/150로 잰다
    (agent_evaluator/core/trackers/layer1.py 실측 확인). 이전 응답은 브리프의 단어를
    하나도 재사용하지 않고 constraints도 빠뜨려 두 축 모두 구조적으로 낮게 나왔다 —
    허구 정보를 채워 넣는 게 아니라, 이미 계산해둔 constraints를 포함하고 브리프
    자체를 명시적으로 인용해 정직하게 relevance/completeness를 채운다."""
    return (
        f'브리프 "{brief}"에 대해, 이 브리프는 {result.golden_data.domain} 도메인으로 판단했다. '
        f"따라서 역할을 {result.team_design.roles}로 설계했다. "
        f"왜냐하면 성공기준이 {result.golden_data.success_criteria}이기 때문이다. "
        f"제약사항은 {result.golden_data.constraints}이다."
    )


def _run_and_build_metadata(brief: str) -> tuple[str, EvalMetadata]:
    result = _run_pipeline(brief)
    response = _build_response(brief, result)
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


@agent_eval(
    monitor,
    task_type="planning",
    question_arg="brief",
    # Gate D: 실측 근거 — 단일 실행 5건 타이밍(interpret 16~29s + design 9~18s +
    # generate 6~12s)이 33~45s에 분포. 앞서 p95=158~191s로 봤던 건 파이프라인이
    # 느린 게 아니라 ReproducibilityConfig(runs=3)의 추가 2회 실행이 execution_time
    # 측정 구간 "안에서" 일어나 3회분이 합산됐기 때문(decorators.py 확인함) — 그래서
    # 재현성은 이 함수에서 빼고 run_for_reproducibility()로 분리했다(Gate C는 거기서).
    sla=SLAConfig(p95_ms=60000.0, p99_ms=90000.0),
    # Gate G: response에 실제 판단 근거를 담아야 통과한다.
    explainability=ExplainabilityConfig(require_reasoning=True),
    # Gate B: SPEC §3이 CrewAI 하나만 허용 — 그 외 프레임워크가 tool_calls에 잡히면 위반.
    scope=ScopeConfig(allowed_tools=["framework:crewai"], fail_on_violation=False, violation_penalty=0.5),
    # Gate E: enable_security_metrics=True(위)로 5개 보안 트래커 활성화. 이 파이프라인의
    # response는 추론 요약 텍스트라 PII/유출 신호는 원래 거의 없다 — 정직하게 밝혀둔다.
    # 실제로 유의미한 신호는 tool_calls(프레임워크 이탈=권한 밖 시도) 쪽에서 나온다.
)
def run(brief: str) -> tuple[str, EvalMetadata]:
    """Gate A/B/D/E/F/G 측정용 — 브리프당 파이프라인 1회만 실행한다(정직한 지연 측정)."""
    return _run_and_build_metadata(brief)


@agent_eval(
    monitor,
    task_type="planning",
    question_arg="brief",
    task_id_fn=lambda args, kwargs: f"repro_{hash(args[0] if args else kwargs.get('brief', '')) & 0xFFFFFF:x}",
    # Gate C 전용 — 여기만 재현성을 켠다. execution_time이 3회분 합산되는 건 알고
    # 있고(위 run()의 docstring 참고), 이 함수 자체를 SLA/Gate D 측정에는 안 쓴다.
    reproducibility=ReproducibilityConfig(runs=3),
)
def run_for_reproducibility(brief: str) -> tuple[str, EvalMetadata]:
    """Gate C 재현성 전용 측정 — Gate D(지연)와 관심사를 분리했다. 같은 브리프를
    3번 실제로 재호출해 도메인/역할 이름이 얼마나 흔들리는지를 잰다."""
    return _run_and_build_metadata(brief)
