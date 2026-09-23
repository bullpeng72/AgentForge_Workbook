"""AgentForge Web UI — SPEC.md F9-F12.

ADR_T-D8D8CE.md 결정 5(정정본) — `agent_evaluator/serve/autopilot_app.py`(port 8766)와
"동일 패턴"을 실제로 재사용한다: FastAPI + 순수 서버 렌더 HTML(f-string + `html.escape`),
Jinja2 엔진은 안 쓴다(그 파일 자체가 안 쓴다는 걸 확인했다 — SPEC의 "Jinja2" 표기는
정정 완료). 새 판정 로직 없음(원칙4) — `compose()`·`gate_lookup`·
`agent_evaluator.gates.autopilot_state`가 이미 계산한 걸 보여주기만 한다.
"""
from __future__ import annotations

from html import escape as _esc
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from agent_evaluator.gates.autopilot_state import PHASE_LABELS, load_all_tasks, load_approvals

from agentforge.pool.composer import compose
from agentforge.pool.gate_lookup import find_run_harness_groups_for_task
from agentforge.pool.index import PoolIndex


def create_app(
    pool: PoolIndex,
    *,
    results_dir: str | Path = "results",
    aoo_dir: str | Path = ".aoo",
) -> FastAPI:
    results_dir = Path(results_dir)
    aoo_dir = Path(aoo_dir)

    app = FastAPI(title="AgentForge")

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        body = """
<h1>AgentForge</h1>
<p class="eyebrow">자연어 브리프 → CrewAI 멀티에이전트 팀</p>
<div class="card">
  <h2>화면</h2>
  <ul>
    <li><a href="/pool">Pool 브라우저</a> — 재사용 가능한 에이전트를 역할·도메인·Gate 점수로 찾는다(F9)</li>
    <li><a href="/compose">팀 구성</a> — 도메인과 필요한 역할을 넣으면 Pool 재사용 여부를 바로 보여준다(F10)</li>
    <li><a href="/evaluate">평가 결과</a> — 실행별 Gate A-G 스코어카드(F11)</li>
    <li><a href="/approvals">승인 현황</a> — Autopilot phase·승인 대기 상태(F12)</li>
  </ul>
</div>
"""
        return _layout("home", "AgentForge", body)

    @app.get("/pool", response_class=HTMLResponse)
    def pool_browser(role: str = "", domain: str = "", gate: str = "", min_score: str = "") -> str:
        contracts = pool.all()

        if role:
            contracts = [c for c in contracts if role.lower() in c.role.lower()]
        if domain:
            contracts = [c for c in contracts if domain.lower() in c.domain.lower()]

        min_score_val: float | None = None
        if min_score:
            try:
                min_score_val = float(min_score)
            except ValueError:
                min_score_val = None

        rows: list[str] = []
        for c in contracts:
            run_info = (
                find_run_harness_groups_for_task(c.origin_task_id, results_dir=results_dir)
                if c.origin_task_id
                else None
            )
            gate_cell, run_file = _render_gate_cell(run_info, gate)

            if gate and min_score_val is not None:
                measured = _gate_score(run_info, gate)
                if measured is None or measured < min_score_val:
                    continue

            rows.append(
                f"<tr><td>{_esc(c.role)}</td><td>{_esc(c.domain)}</td>"
                f"<td>{_esc(c.source_task_id)}</td><td>{_esc(run_file or '—')}</td>"
                f"<td>{gate_cell}</td></tr>"
            )

        table = (
            "<table><thead><tr><th>역할</th><th>도메인</th><th>Pool ID</th>"
            "<th>측정된 실행</th><th>Gate 점수</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            if rows
            else '<p class="empty">조건에 맞는 pool 항목이 없습니다.</p>'
        )

        body = f"""
<h1>Pool 브라우저</h1>
<p class="eyebrow">F9 — 역할 · 도메인 · Gate 점수로 검색</p>
<div class="card">
  <form class="inline" method="get" action="/pool">
    <div class="field"><label>역할</label><input type="text" name="role" value="{_esc(role)}"></div>
    <div class="field"><label>도메인</label><input type="text" name="domain" value="{_esc(domain)}"></div>
    <div class="field"><label>Gate</label>
      <select name="gate">
        <option value="">(선택 안 함)</option>
        {"".join(f'<option value="{g}" {"selected" if gate == g else ""}>{g}</option>' for g in "ABCDEFG")}
        <option value="overall" {"selected" if gate == "overall" else ""}>overall</option>
      </select>
    </div>
    <div class="field"><label>최소 점수</label><input type="text" name="min_score" value="{_esc(min_score)}" placeholder="0.7"></div>
    <button type="submit">검색</button>
  </form>
</div>
<div class="card">
  <h2>결과 ({len(rows)}건)</h2>
  {table}
</div>
"""
        return _layout("pool", "Pool 브라우저", body)

    @app.get("/compose", response_class=HTMLResponse)
    def compose_screen(domain: str = "", roles: str = "") -> str:
        role_list = [r.strip() for r in roles.split(",") if r.strip()]
        decisions_html = ""
        if domain and role_list:
            result = compose(domain=domain, roles=role_list, pool=pool)
            items = []
            for d in result.decisions:
                items.append(
                    f'<div class="approval-item"><span class="badge {_action_class(d.action)}">{_esc(d.action)}</span> '
                    f"<b>{_esc(d.role)}</b><p class=\"tm\">{_esc(d.note)}</p></div>"
                )
            decisions_html = (
                f'<div class="card"><h2>판단 결과</h2>{"".join(items)}'
                f'<p class="tm">신규 생성 필요: {_esc(", ".join(result.roles_to_generate) or "없음")}</p></div>'
            )

        body = f"""
<h1>팀 구성</h1>
<p class="eyebrow">F10 — 도메인 + 필요한 역할을 넣으면 Pool 재사용 여부를 바로 보여준다(3단 에스컬레이션)</p>
<div class="card">
  <form class="inline" method="get" action="/compose">
    <div class="field"><label>도메인</label><input type="text" name="domain" value="{_esc(domain)}" placeholder="support"></div>
    <div class="field"><label>필요한 역할(쉼표 구분)</label>
      <input type="text" name="roles" value="{_esc(roles)}" placeholder="Classifier, Translator"></div>
    <button type="submit">호환성 확인</button>
  </form>
</div>
{decisions_html}
"""
        return _layout("compose", "팀 구성", body)

    @app.get("/evaluate", response_class=HTMLResponse)
    def evaluate_list() -> str:
        rows = []
        for path in sorted(results_dir.glob("*.json")) if results_dir.is_dir() else []:
            groups = _read_harness_groups(path)
            if groups is None:
                continue
            overall = groups.get("overall", {})
            rows.append(
                f'<tr><td><a href="/evaluate/{_esc(path.name)}">{_esc(path.name)}</a></td>'
                f'<td><span class="badge {_esc(str(overall.get("status", "")))}">'
                f'{_esc(str(overall.get("status", "—")))}</span></td>'
                f'<td>{_esc(str(overall.get("score", "—")))}</td></tr>'
            )
        table = (
            "<table><thead><tr><th>파일</th><th>상태</th><th>overall</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            if rows
            else '<p class="empty">results/ 아래에 Gate A-G가 측정된 실행이 없습니다.</p>'
        )
        body = f"""
<h1>평가 결과</h1>
<p class="eyebrow">F11 — 실행별 Gate A-G 스코어카드</p>
<div class="card">{table}</div>
"""
        return _layout("evaluate", "평가 결과", body)

    @app.get("/evaluate/{filename}", response_class=HTMLResponse)
    def evaluate_detail(filename: str) -> str:
        # 경로 이탈 방지 — filename은 results_dir 바로 아래 파일만 가리켜야 한다.
        path = results_dir / Path(filename).name
        groups = _read_harness_groups(path) if path.is_file() else None
        if groups is None:
            body = f'<h1>평가 결과</h1><p class="empty">{_esc(filename)}을(를) 읽을 수 없습니다.</p>'
            return _layout("evaluate", "평가 결과", body)

        rows = "".join(
            f'<tr><td>{_esc(gate)}</td><td><span class="badge {_esc(str(v.get("status", "")))}">'
            f'{_esc(str(v.get("status", "—")))}</span></td><td>{_esc(str(v.get("score", "—")))}</td></tr>'
            for gate, v in groups.items()
            if isinstance(v, dict)
        )
        body = f"""
<h1>{_esc(filename)}</h1>
<p class="eyebrow">F11 — Gate A-G 스코어카드</p>
<div class="card">
  <table><thead><tr><th>Gate</th><th>상태</th><th>점수</th></tr></thead><tbody>{rows}</tbody></table>
</div>
<p><a href="/evaluate">&larr; 목록으로</a></p>
"""
        return _layout("evaluate", filename, body)

    @app.get("/approvals", response_class=HTMLResponse)
    def approvals_status() -> str:
        tasks = load_all_tasks(aoo_dir / "tasks") if (aoo_dir / "tasks").is_dir() else []
        approvals_path = aoo_dir / "approvals.jsonl"
        approvals = load_approvals(approvals_path) if approvals_path.is_file() else []

        task_rows = "".join(
            f'<tr><td>{_esc(str(t.get("task_id")))}</td><td>{_esc(str(t.get("title")))}</td>'
            f'<td>phase {_esc(str(t.get("current_phase")))} '
            f'({_esc(PHASE_LABELS.get(t.get("current_phase"), "—"))})</td></tr>'
            for t in tasks
        )
        approval_items = "".join(
            f'<div class="approval-item"><span class="badge {_esc(str(a.get("status", "")))}">'
            f'{_esc(str(a.get("status", "")))}</span> {_esc(str(a.get("title")))} '
            f'<span class="tm">({_esc(str(a.get("kind")))}, task={_esc(str(a.get("task_id")))})</span></div>'
            for a in approvals
        )

        body = f"""
<h1>승인 현황</h1>
<p class="eyebrow">F12 — 이 팀이 어느 Autopilot phase·승인 단계에 있는가</p>
<div class="card">
  <h2>과제</h2>
  {f'<table><thead><tr><th>ID</th><th>제목</th><th>Phase</th></tr></thead><tbody>{task_rows}</tbody></table>' if task_rows else '<p class="empty">과제가 없습니다.</p>'}
</div>
<div class="card">
  <h2>승인 이력</h2>
  {approval_items or '<p class="empty">승인 이력이 없습니다.</p>'}
</div>
"""
        return _layout("approvals", "승인 현황", body)

    return app


def _read_harness_groups(path: Path) -> dict[str, Any] | None:
    import json

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    groups = data.get("extra_metrics", {}).get("harness_groups")
    return groups if isinstance(groups, dict) else None


def _gate_score(run_info: tuple[str, dict[str, Any]] | None, gate: str) -> float | None:
    if run_info is None or not gate:
        return None
    _filename, groups = run_info
    entry = groups.get(gate)
    if not isinstance(entry, dict):
        return None
    score = entry.get("score")
    return float(score) if isinstance(score, (int, float)) else None


def _render_gate_cell(run_info: tuple[str, dict[str, Any]] | None, gate: str) -> tuple[str, str | None]:
    if run_info is None:
        return '<span class="tm">미측정</span>', None
    filename, groups = run_info
    if not gate:
        overall = groups.get("overall", {})
        return (
            f'<span class="badge {_esc(str(overall.get("status", "")))}">'
            f'{_esc(str(overall.get("score", "—")))}</span>',
            filename,
        )
    entry = groups.get(gate, {})
    if not isinstance(entry, dict):
        return '<span class="tm">미측정</span>', filename
    return (
        f'<span class="badge {_esc(str(entry.get("status", "")))}">'
        f'{gate}={_esc(str(entry.get("score", "—")))}</span>',
        filename,
    )


def _action_class(action: str) -> str:
    return {
        "reuse_exact": "pass",
        "reuse_adapted": "pass",
        "flag_for_human": "pending",
        "generate_new": "draft",
    }.get(action, "")


_STYLE = """
:root{
  --paper:#F3F4F1; --paper-raised:#FFFFFF; --paper-sunken:#E9EBE7;
  --ink:#14181D; --ink-dim:#5B6169; --ink-faint:#8B9198;
  --line:#DCDFDB; --accent-h:#B85420; --accent-a:#2E5A7A; --accent-a-soft:#DCE6EC;
  --success:#2E7D46; --success-soft:#DDEEE1;
  --warning:#96661C; --warning-soft:#F1E4C6;
  --critical:#B23B3B; --critical-soft:#F5DEDE;
}
*{box-sizing:border-box;}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:'IBM Plex Sans KR','IBM Plex Sans',-apple-system,'Segoe UI',sans-serif;
  font-size:14.5px;line-height:1.55;}
a{color:var(--accent-a);}
.shell{max-width:920px;margin:0 auto;padding:20px 20px 60px;}
.nav{display:flex;gap:4px;align-items:center;padding:12px 20px;
  border-bottom:1px solid var(--line);background:var(--paper-raised);flex-wrap:wrap;}
.nav .brand{font-weight:800;font-family:monospace;font-size:13px;margin-right:16px;color:var(--accent-h);}
.nav a{text-decoration:none;color:var(--ink-dim);padding:6px 12px;border-radius:8px;
  font-size:13px;font-weight:600;}
.nav a.active{background:var(--ink);color:var(--paper);}
h1{font-size:20px;margin:18px 0 4px;}
.eyebrow{font-family:monospace;font-size:11px;color:var(--accent-h);letter-spacing:.06em;
  text-transform:uppercase;font-weight:700;}
.card{background:var(--paper-raised);border:1px solid var(--line);border-radius:12px;
  padding:16px;margin-bottom:18px;}
.card h2{font-size:14.5px;margin:0 0 10px;}
table{width:100%;border-collapse:collapse;font-size:13px;}
th{text-align:left;font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;
  color:var(--ink-faint);padding:0 8px 6px;}
td{padding:8px;border-top:1px solid var(--line);font-family:monospace;font-size:12.5px;vertical-align:top;}
.empty{color:var(--ink-faint);font-size:12.5px;padding:6px 0;}
.badge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:10.5px;font-weight:700;
  background:var(--accent-a-soft);color:var(--accent-a);}
.badge.pass{background:var(--success-soft);color:var(--success);}
.badge.warn,.badge.pending{background:var(--warning-soft);color:var(--warning);}
.badge.fail,.badge.rejected{background:var(--critical-soft);color:var(--critical);}
.badge.draft{background:var(--paper-sunken);color:var(--ink-faint);}
form.inline{display:flex;gap:8px;flex-wrap:wrap;align-items:flex-end;}
.field{display:flex;flex-direction:column;gap:4px;}
.field label{font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink-faint);font-weight:700;}
input[type=text],select{border:1px solid var(--line);border-radius:8px;padding:7px 9px;
  font:inherit;font-size:12.8px;background:var(--paper-sunken);color:var(--ink);}
button{border:1px solid var(--ink);background:var(--ink);color:var(--paper);border-radius:8px;
  padding:8px 14px;font-size:12.5px;font-weight:700;cursor:pointer;font-family:inherit;}
.approval-item{border:1px solid var(--line);border-radius:12px;padding:12px;margin-bottom:10px;
  background:var(--paper-raised);}
.tm{font-family:monospace;font-size:11.3px;color:var(--ink-dim);}
"""

_NAV_ITEMS = [
    ("home", "/", "홈"),
    ("pool", "/pool", "Pool"),
    ("compose", "/compose", "팀 구성"),
    ("evaluate", "/evaluate", "평가 결과"),
    ("approvals", "/approvals", "승인 현황"),
]


def _nav(active: str) -> str:
    links = "".join(
        f'<a href="{href}" class="{"active" if key == active else ""}">{label}</a>'
        for key, href, label in _NAV_ITEMS
    )
    return f'<div class="nav"><span class="brand">AGENTFORGE</span>{links}</div>'


def _layout(active: str, title: str, body: str) -> str:
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{_esc(title)} — AgentForge</title>
<style>{_STYLE}</style></head>
<body>
{_nav(active)}
<div class="shell">
{body}
</div>
</body></html>"""
