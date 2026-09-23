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
) -> PipelineResult:
    """v1 파이프라인: Spec Interpreter·Team Designer는 Tier 1 LLM, Code Generator·
    Verifier는 아직 v0 그대로(템플릿/구문체크) — v2(Part VI 후반)에서 실제화된다.

    Composer(F5-F8, Pool 재사용)는 v4(Part X)부터 이 앞단에 들어간다 — 아직 없다.
    """
    golden_data = interpret(brief, client=interpreter_client)
    team_design = design(golden_data, client=designer_client)
    generated = generate(team_design)
    verification = verify(generated)
    return PipelineResult(
        golden_data=golden_data,
        team_design=team_design,
        generated=generated,
        verification=verification,
    )
