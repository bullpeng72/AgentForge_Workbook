from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from agentforge.pool.contract import AgentContract
from agentforge.pool.index import PoolIndex

Action = Literal["reuse_exact", "reuse_adapted", "flag_for_human", "generate_new"]


@dataclass
class ComposeDecision:
    role: str
    action: Action
    source_contract: AgentContract | None = None
    adapted_agents_yaml_snippet: str | None = None
    note: str = ""


@dataclass
class ComposeResult:
    decisions: list[ComposeDecision]

    @property
    def roles_to_generate(self) -> list[str]:
        """F8 — Pool 부족분(찾지 못한/못 쓴 역할)만 신규 생성 대상이다."""
        return [d.role for d in self.decisions if d.action in ("flag_for_human", "generate_new")]


def compose(domain: str, roles: list[str], pool: PoolIndex) -> ComposeResult:
    """F5-F7 — 새 팀에 필요한 역할마다 Pool 재사용 가능 여부를 3단 에스컬레이션으로
    판단한다. F8(부족분만 신규 생성)은 ComposeResult.roles_to_generate가 담당한다."""
    domain_candidates = pool.search_by_domain(domain)
    decisions: list[ComposeDecision] = []

    for role in roles:
        exact = next((c for c in domain_candidates if _roles_match(c.role, role)), None)
        if exact is not None:
            decisions.append(
                ComposeDecision(role=role, action="reuse_exact", source_contract=exact,
                                 note=f"Pool에서 정확히 일치하는 역할 재사용(source={exact.source_task_id})")
            )
            continue

        if domain_candidates:
            # 2단계: 자동 어댑터 — 같은 도메인의 후보 전원을 훑어 호환되는 첫 번째를
            # 쓴다. 실측(gate_run_pool, Part X): domain_candidates[0] 하나만 보던
            # 이전 버전은 pool에 진짜 맞는 후보(Classifier)가 있어도 그게 첫 항목이
            # 아니면(Sanitizer가 먼저 들어와 있으면) 못 찾고 flag_for_human으로
            # 새버렸다 — GPT-5의 역할 이름이 매 설계마다 크게 흔들려 이 케이스가
            # 실제로 발생했다.
            source = next((c for c in domain_candidates if _plausibly_compatible(c, role)), None)
            if source is not None:
                adapted = _adapt_snippet(source.agents_yaml_snippet, source.role, role)
                decisions.append(
                    ComposeDecision(
                        role=role, action="reuse_adapted", source_contract=source,
                        adapted_agents_yaml_snippet=adapted,
                        note=f"자동 어댑터: {source.role}(source={source.source_task_id})를 {role}로 재라벨링",
                    )
                )
                continue
            # 3단계: 어느 후보와도 못 미더우면 사람에게 넘긴다 — 억지로 재사용하지 않는다.
            decisions.append(
                ComposeDecision(
                    role=role, action="flag_for_human", source_contract=domain_candidates[0],
                    note=(
                        f"같은 도메인({domain})에 후보({len(domain_candidates)}건)는 있지만 어느 것도 "
                        f"역할명과 출력 설명이 충분히 겹치지 않아 자동 재사용하지 않음 — 사람 확인 필요"
                    ),
                )
            )
            continue

        # Pool에 이 도메인 자체가 없음 — F8: 신규 생성 대상
        decisions.append(ComposeDecision(role=role, action="generate_new", note="Pool에 같은 도메인 후보 없음"))

    return ComposeResult(decisions=decisions)


def _roles_match(pool_role: str, needed_role: str) -> bool:
    return pool_role.strip().lower() == needed_role.strip().lower()


def _plausibly_compatible(source: AgentContract, needed_role: str) -> bool:
    """아주 단순한 호환성 휴리스틱 — 새 역할명의 각 단어(카멜케이스 분리)가 기존
    계약의 output_description 단어와 접두어를 공유하지 않으면 자동 재사용을
    거부한다(예: "Reviewer" vs "review" — 단순 포함 검사로는 "reviewer"가
    "review"보다 길어 놓친다, 실측 테스트로 잡은 버그). 완벽한 의미 매칭이 아니라,
    명백히 무관한 재사용을 걸러내는 최소 안전장치다."""
    import re

    words = [w.lower() for w in re.findall(r"[A-Z][a-z]*|[a-z]+", needed_role)]
    if not words:
        return True
    output_tokens = re.findall(r"[a-zA-Z]+", source.output_description.lower())
    return any(w.startswith(t) or t.startswith(w) for w in words for t in output_tokens)


def _adapt_snippet(snippet: str, old_role: str, new_role: str) -> str:
    return snippet.replace(old_role, new_role)
