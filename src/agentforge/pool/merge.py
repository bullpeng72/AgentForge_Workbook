from __future__ import annotations

import yaml


def merge_agents_yaml(reused_snippets: list[str], generated_yaml: str | None) -> str:
    """재사용 스니펫들 + 신규 생성분의 agents 목록을 하나의 agents.yaml로 합친다.
    F8: 부족분만 생성했으니, 최종 결과물은 반드시 합쳐진 형태여야 한다."""
    all_agents: list[dict] = []
    for snippet in reused_snippets:
        parsed = yaml.safe_load(snippet) or {}
        if isinstance(parsed, dict):
            all_agents.extend(a for a in parsed.get("agents", []) if isinstance(a, dict))

    if generated_yaml:
        parsed = yaml.safe_load(generated_yaml) or {}
        if isinstance(parsed, dict):
            all_agents.extend(a for a in parsed.get("agents", []) if isinstance(a, dict))

    return yaml.safe_dump({"agents": all_agents}, allow_unicode=True, sort_keys=False)
