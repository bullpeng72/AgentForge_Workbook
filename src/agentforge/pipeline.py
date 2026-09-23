from __future__ import annotations

import uuid
from dataclasses import dataclass, field

import yaml

from agentforge.code_generator.generator import GeneratedCode, generate
from agentforge.llm.client import LLMClient
from agentforge.pool.composer import ComposeResult, compose
from agentforge.pool.contract import AgentContract
from agentforge.pool.index import PoolIndex
from agentforge.pool.merge import merge_agents_yaml
from agentforge.spec_interpreter.interpreter import GoldenData, interpret
from agentforge.team_designer.designer import TeamDesign, design
from agentforge.verifier.verifier import VerificationResult, verify


@dataclass
class PipelineResult:
    golden_data: GoldenData
    team_design: TeamDesign
    generated: GeneratedCode
    verification: VerificationResult
    compose_result: ComposeResult | None = field(default=None)


def run(
    brief: str,
    *,
    pool: PoolIndex | None = None,
    interpreter_client: LLMClient | None = None,
    designer_client: LLMClient | None = None,
    generator_client: LLMClient | None = None,
) -> PipelineResult:
    """v4 파이프라인: pool을 주면 F5-F8(Pool 재사용)이 Code Generator 앞단에 들어간다 —
    안 주면 v3와 동일하게(전부 신규 생성) 동작한다(하위 호환).

    F8: Pool에서 못 찾은/못 쓴 역할만 실제로 Code Generator(LLM)를 호출한다 —
    전체 재생성 금지.
    """
    golden_data = interpret(brief, client=interpreter_client)
    team_design = design(golden_data, client=designer_client)

    if pool is None:
        generated = generate(team_design, client=generator_client)
        verification = verify(generated, golden_data)
        return PipelineResult(golden_data, team_design, generated, verification, compose_result=None)

    compose_result = compose(golden_data.domain, team_design.roles, pool)
    roles_to_generate = compose_result.roles_to_generate

    reused_snippets = [
        d.adapted_agents_yaml_snippet or d.source_contract.agents_yaml_snippet
        for d in compose_result.decisions
        if d.action in ("reuse_exact", "reuse_adapted") and d.source_contract is not None
    ]

    generated_new: GeneratedCode | None = None
    if roles_to_generate:
        partial_design = TeamDesign(domain=team_design.domain, roles=roles_to_generate)
        generated_new = generate(partial_design, client=generator_client)

    merged_yaml = merge_agents_yaml(
        reused_snippets, generated_new.agents_yaml if generated_new else None
    )
    merged_crew_py = generated_new.crew_py if generated_new else "from crewai import Agent, Task, Crew\n"
    generated = GeneratedCode(agents_yaml=merged_yaml, crew_py=merged_crew_py)

    verification = verify(generated, golden_data)

    if verification.passed:
        _populate_pool(pool, golden_data, roles_to_generate, generated_new)

    return PipelineResult(golden_data, team_design, generated, verification, compose_result)


def _populate_pool(
    pool: PoolIndex, golden_data: GoldenData, new_roles: list[str], generated_new: GeneratedCode | None
) -> None:
    """검증 통과한 신규 생성 에이전트만 Pool에 추가한다 — 재사용해온 것은 이미
    있으므로 다시 넣지 않는다.

    한 번의 generate() 호출이 여러 역할을 동시에 만들면 generated_new.agents_yaml에
    전부 합쳐져 있다 — 그 전체를 각 역할의 snippet으로 통째로 저장하면, 나중에
    두 역할이 각각 재사용될 때 merge_agents_yaml이 같은 에이전트들을 중복으로
    합치게 된다. 역할별로 자기 항목만 잘라서 저장한다."""
    if not generated_new or not new_roles:
        return

    parsed = yaml.safe_load(generated_new.agents_yaml) or {}
    all_agents = parsed.get("agents", []) if isinstance(parsed, dict) else []

    for role in new_roles:
        own_entry = next(
            (a for a in all_agents if isinstance(a, dict) and a.get("role") == role), None
        )
        snippet = (
            yaml.safe_dump({"agents": [own_entry]}, allow_unicode=True, sort_keys=False)
            if own_entry is not None
            else generated_new.agents_yaml  # 못 찾으면(이례적) 전체를 보수적으로 저장
        )
        pool.add(
            AgentContract(
                role=role,
                domain=golden_data.domain,
                input_description=golden_data.goal,
                output_description=f"{role} 역할: {golden_data.success_criteria}",
                source_task_id=f"pool-{uuid.uuid4().hex[:12]}",
                agents_yaml_snippet=snippet,
            )
        )
