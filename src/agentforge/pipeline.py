from __future__ import annotations

from dataclasses import dataclass

from agentforge.code_generator.generator import GeneratedCode, generate
from agentforge.spec_interpreter.interpreter import GoldenData, interpret
from agentforge.team_designer.designer import TeamDesign, design
from agentforge.verifier.verifier import VerificationResult, verify


@dataclass
class PipelineResult:
    golden_data: GoldenData
    team_design: TeamDesign
    generated: GeneratedCode
    verification: VerificationResult


def run(brief: str) -> PipelineResult:
    """v0 파이프라인: Spec Interpreter → Team Designer → Code Generator → Verifier.

    Composer(F5-F8, Pool 재사용)는 v4(Part X)부터 이 앞단에 들어간다 — v0에는 없다.
    """
    golden_data = interpret(brief)
    team_design = design(golden_data)
    generated = generate(team_design)
    verification = verify(generated)
    return PipelineResult(
        golden_data=golden_data,
        team_design=team_design,
        generated=generated,
        verification=verification,
    )
