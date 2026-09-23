from __future__ import annotations

from pydantic import BaseModel


class AgentContract(BaseModel):
    """ADR_T-D8D8CE.md 결정 3 — Pydantic v2로 확정. 에이전트 하나의 재사용 가능
    단위를 나타낸다. CrewAI agents.yaml 자체엔 형식화된 입출력 타입이 없어(자유
    텍스트 goal/backstory), 이 계약은 그 텍스트에서 뽑아낸 "이 역할이 어떤 입력을
    다루고 어떤 출력을 내는가"에 대한 가벼운 서술이다 — 엄격한 타입 검증기가
    아니라, Composer가 재사용 여부를 판단할 근거."""

    role: str
    domain: str
    input_description: str
    output_description: str
    source_task_id: str
    agents_yaml_snippet: str
    # ADR 결정 6(Part XI) — source_task_id는 pool 항목 자체의 PK(역할별로 고유해야
    # 함)라 results/*.json의 실제 평가 task_id와 다르다(한 번의 호출이 여러 역할을
    # 만들면 여러 역할이 같은 실행을 공유). Gate 점수를 results/*.json에서 역참조할
    # 때는 이 필드를 쓴다 — None이면 그 항목을 만든 실행의 원 task_id를 모른다는 뜻
    # (예: 오프라인 테스트가 직접 add()한 경우).
    origin_task_id: str | None = None


def domains_match(a: AgentContract, domain: str) -> bool:
    return a.domain == domain


def roles_match_exactly(a: AgentContract, role: str) -> bool:
    return a.role.strip().lower() == role.strip().lower()
