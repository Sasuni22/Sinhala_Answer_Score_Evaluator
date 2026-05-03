"""
Agent-based architecture for the SinhalaScore AI system.
Fixed: timeout wrapper, reduced tokens, coverage via keyword matching only,
       robust JSON extraction with truncation recovery.
"""

import json
import re
import threading
import ollama
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentMessage:
    question_id: str
    question_sinhala: str
    student_answer: str
    marking_guide: list[dict]
    retrieved_context: str = ""
    ontology_concepts: list[dict] = field(default_factory=list)
    coverage_report: dict = field(default_factory=dict)
    score_breakdown: list[dict] = field(default_factory=list)
    final_score: int = 0
    explanation: str = ""
    error: Optional[str] = None


class BaseAgent(ABC):
    def __init__(self, name: str, model: str = "gemma3:1b"):
        self.name = name
        self.model = model

    def call_ollama(self, system_prompt: str, user_prompt: str,
                    max_tokens: int = 600, timeout_secs: int = 25) -> str:
        """Call Ollama with a hard timeout so Streamlit never hangs."""
        result = ["ERROR:TIMEOUT"]

        def _call():
            try:
                response = ollama.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt},
                    ],
                    options={
                        "num_predict": max_tokens,
                        "temperature": 0.1,
                        "stop": ["```", "Note:", "Explanation:", "Here", "The student"],
                    },
                )
                result[0] = response["message"]["content"].strip()
            except Exception as e:
                err = str(e)
                if any(k in err for k in ["10061", "Connection refused", "connect"]):
                    result[0] = "ERROR:OLLAMA_OFFLINE"
                else:
                    result[0] = f"ERROR: {err}"

        t = threading.Thread(target=_call, daemon=True)
        t.start()
        t.join(timeout=timeout_secs)
        return result[0]

    def extract_json(self, raw: str) -> Optional[dict]:
        """Robustly extract the first valid JSON object from model output."""
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start < 0 or end <= start:
            return None
        fragment = raw[start:end]
        try:
            return json.loads(fragment)
        except json.JSONDecodeError:
            pass
        # Attempt to recover truncated JSON
        open_brackets = fragment.count("[") - fragment.count("]")
        open_braces   = fragment.count("{") - fragment.count("}")
        if fragment.count('"') % 2 != 0:
            fragment += '"'
        fragment += "]" * max(open_brackets, 0)
        fragment += "}" * max(open_braces,   0)
        try:
            return json.loads(fragment)
        except Exception:
            return None

    @abstractmethod
    def run(self, msg: AgentMessage) -> AgentMessage:
        pass


# ── Agent 1: Coverage Checker ─────────────────────────────────────────────────
class CoverageCheckerAgent(BaseAgent):
    """
    Pure keyword-based coverage check — no LLM call.
    gemma3:1b cannot reliably process Sinhala text so we match
    marking-guide keywords directly against the student answer.
    """

    def __init__(self, model: str = "gemma3:1b"):
        super().__init__("CoverageCheckerAgent", model)

    def run(self, msg: AgentMessage) -> AgentMessage:
        criteria_coverage = []
        missing = []
        covered_count = 0

        for c in msg.marking_guide:
            keywords = c.get("keywords", [])

            if not keywords:
                criteria_coverage.append({
                    "criteria": c["criteria"],
                    "covered": True,
                    "evidence": "Language criterion — assessed by scorer agent",
                })
                covered_count += 1
                continue

            matched = [kw for kw in keywords if kw in msg.student_answer]
            covered = len(matched) > 0
            if covered:
                covered_count += 1
            else:
                missing.append(c["criteria"])

            criteria_coverage.append({
                "criteria": c["criteria"],
                "covered": covered,
                "evidence": f"Matched: {matched[:3]}" if matched else "No keywords found",
            })

        total = max(len(msg.marking_guide), 1)
        msg.coverage_report = {
            "criteria_coverage": criteria_coverage,
            "overall_coverage_percent": round((covered_count / total) * 100),
            "missing_topics": missing,
        }
        return msg


# ── Agent 2: Scorer ───────────────────────────────────────────────────────────
class ScorerAgent(BaseAgent):

    def __init__(self, model: str = "gemma3:1b"):
        super().__init__("ScorerAgent", model)

    def run(self, msg: AgentMessage) -> AgentMessage:
        guide_lines = "\n".join(
            f"{i+1}. {c['criteria']} (max {c['marks']})"
            for i, c in enumerate(msg.marking_guide)
        )
        ontology_terms = (
            ", ".join(c["keyword"] for c in msg.ontology_concepts) or "none"
        )
        coverage_pct = msg.coverage_report.get("overall_coverage_percent", 50)
        answer_len   = len(msg.student_answer)

        system = (
            "You are a history exam scorer. "
            "Return ONLY a valid JSON object — no text before or after."
        )
        user = (
            f"Answer length: {answer_len} chars. "
            f"Keyword coverage: {coverage_pct}%. "
            f"Historical terms found: {ontology_terms}.\n\n"
            f"Criteria:\n{guide_lines}\n\n"
            "Score every criterion above. "
            "Return JSON only — no explanation:\n"
            '{"breakdown":['
            '{"criteria":"...","max_marks":4,"awarded_marks":2,"justification":"..."}'
            "]}"
        )

        raw    = self.call_ollama(system, user, max_tokens=500, timeout_secs=25)
        scored = None

        if not raw.startswith("ERROR"):
            parsed = self.extract_json(raw)
            if (parsed
                    and "breakdown" in parsed
                    and isinstance(parsed["breakdown"], list)
                    and len(parsed["breakdown"]) > 0
                    and all("criteria" in b and "max_marks" in b and "awarded_marks" in b
                            for b in parsed["breakdown"])):
                scored = parsed

        if scored is None:
            scored = self._fallback_score(msg)

        msg.score_breakdown = scored["breakdown"]
        msg.final_score = min(
            sum(b.get("awarded_marks", 0) for b in msg.score_breakdown), 20
        )
        return msg

    def _fallback_score(self, msg: AgentMessage) -> dict:
        """Keyword-ratio fallback when LLM output is unusable."""
        breakdown = []
        for c in msg.marking_guide:
            keywords  = c.get("keywords", [])
            max_marks = c["marks"]
            if not keywords:
                awarded = max(1, max_marks - 1)
            else:
                matched = sum(1 for kw in keywords if kw in msg.student_answer)
                awarded = round((matched / len(keywords)) * max_marks)
            breakdown.append({
                "criteria":      c["criteria"],
                "max_marks":     max_marks,
                "awarded_marks": awarded,
                "justification": f"Keyword match {awarded}/{max_marks}",
            })
        return {"breakdown": breakdown}


# ── Agent 3: Explanation ──────────────────────────────────────────────────────
class ExplanationAgent(BaseAgent):

    def __init__(self, model: str = "gemma3:1b"):
        super().__init__("ExplanationAgent", model)

    def run(self, msg: AgentMessage) -> AgentMessage:
        score   = msg.final_score
        max_tot = sum(b.get("max_marks", 0) for b in msg.score_breakdown)
        missing = msg.coverage_report.get("missing_topics", [])

        weakest = min(
            msg.score_breakdown,
            key=lambda b: b.get("awarded_marks", 0) / max(b.get("max_marks", 1), 1),
            default=None,
        )
        weakest_name = weakest["criteria"][:50] if weakest else "N/A"
        missing_str  = ", ".join(missing[:3]) if missing else "none"

        system = (
            "You are a friendly history teacher. "
            "Give brief student feedback in exactly 3 bullet points."
        )
        user = (
            f"Score: {score}/{max_tot}. "
            f"Weakest area: {weakest_name}. "
            f"Missing topics: {missing_str}.\n"
            "Write:\n"
            "• Strength: one thing done well\n"
            "• Weakness: one thing missing\n"
            "• Tip: one concrete improvement\n"
            "Max 70 words total."
        )

        feedback = self.call_ollama(system, user, max_tokens=250, timeout_secs=20)

        if feedback.startswith("ERROR") or len(feedback.strip()) < 15:
            feedback = self._fallback_explanation(msg)

        msg.explanation = feedback
        return msg

    def _fallback_explanation(self, msg: AgentMessage) -> str:
        lines = [f"**Score: {msg.final_score}/20**\n"]
        for b in msg.score_breakdown:
            lines.append(
                f"• {b['criteria']}: {b['awarded_marks']}/{b['max_marks']}"
                f" — {b.get('justification', '')}"
            )
        missing = msg.coverage_report.get("missing_topics", [])
        if missing:
            lines.append(f"\n**Missing topics:** {', '.join(missing)}")
        ontology = [c["keyword"] for c in msg.ontology_concepts]
        if ontology:
            lines.append(f"\n**Historical terms used:** {', '.join(ontology)}")
        return "\n".join(lines)


# ── Agent 4: Consistency Checker ──────────────────────────────────────────────
class ConsistencyCheckerAgent(BaseAgent):

    def __init__(self, model: str = "gemma3:1b"):
        super().__init__("ConsistencyCheckerAgent", model)

    def run(self, msg: AgentMessage) -> AgentMessage:
        if msg.score_breakdown:
            total = sum(b.get("awarded_marks", 0) for b in msg.score_breakdown)
            msg.final_score = min(max(total, 0), 20)
        else:
            fallback_agent = ScorerAgent(model=self.model)
            fallback = fallback_agent._fallback_score(msg)
            msg.score_breakdown = fallback["breakdown"]
            msg.final_score = min(
                sum(b.get("awarded_marks", 0) for b in msg.score_breakdown), 20
            )
        return msg