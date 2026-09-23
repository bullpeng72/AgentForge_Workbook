from __future__ import annotations

from dataclasses import dataclass

from agentforge.code_generator.generator import GeneratedCode, generate
from agentforge.llm.client import LLMClient
from agentforge.spec_interpreter.interpreter import GoldenData, interpret
from agentforge.team_designer.designer import TeamDesign, design
from agentforge.verifier.verifier import VerificationResult, verify


@dataclass
class PipelineResult:
    golden_data: GoldenData
    team_design: TeamDesign
    generated: GeneratedCode
    verification: VerificationResult


def run(
    brief: str,
    *,
    interpreter_client: LLMClient | None = None,
    designer_client: LLMClient | None = None,
    generator_client: LLMClient | None = None,
) -> PipelineResult:
    """v3 파이프라인: 4단계 전부 실제 LLM(Tier1: Spec Interpreter·Team Designer,
    Tier2: Code Generator) + Verifier가 crewai.Agent 실제 생성 확인에 더해 결과물용
    골든셋과 `@agent_eval` 배선까지 자동 생성한다(F4).

    Composer(F5-F8, Pool 재사용)는 v4(Part X)부터 이 앞단에 들어간다 — 아직 없다.
    """
    golden_data = interpret(brief, client=interpreter_client)
    team_design = design(golden_data, client=designer_client)
    generated = generate(team_design, client=generator_client)
    verification = verify(generated, golden_data)
    return PipelineResult(
        golden_data=golden_data,
        team_design=team_design,
        generated=generated,
        verification=verification,
    )
