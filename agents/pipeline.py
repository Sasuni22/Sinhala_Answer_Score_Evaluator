"""
Agent Pipeline Orchestrator
Coordinates: RAG → Ontology → Coverage → Scoring → Explanation → Consistency
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.agents import (
    AgentMessage,
    CoverageCheckerAgent,
    ScorerAgent,
    ExplanationAgent,
    ConsistencyCheckerAgent,
)
from rag.retriever import retrieve_context, format_context_for_prompt
from ontology.anuradhapura_ontology import get_ontology_concepts_for_answer


def run_scoring_pipeline(
    question: dict,
    student_answer: str,
    model: str = "gemma3:1b",
    progress_callback=None,
) -> AgentMessage:

    def update(step: str):
        if progress_callback:
            progress_callback(step)

    msg = AgentMessage(
        question_id=question["id"],
        question_sinhala=question["sinhala"],
        student_answer=student_answer,
        marking_guide=question["marking_guide"],
    )

    # Step 1: RAG retrieval — use sinhala question + first 150 chars of answer
    update("Retrieving knowledge context...")
    try:
        combined_query = f"{question['sinhala'][:100]} {student_answer[:150]}"
        contexts = retrieve_context(combined_query, n_results=3)
        msg.retrieved_context = format_context_for_prompt(contexts)
    except Exception as e:
        msg.retrieved_context = ""

    # Step 2: Ontology concept extraction — pure keyword match, never hangs
    update("Extracting ontology concepts...")
    try:
        msg.ontology_concepts = get_ontology_concepts_for_answer(student_answer)
    except Exception:
        msg.ontology_concepts = []

    # Step 3: Coverage check — keyword-based, no LLM call
    update("Checking answer coverage...")
    coverage_agent = CoverageCheckerAgent(model=model)
    msg = coverage_agent.run(msg)

    # Step 4: Scorer — single LLM call with timeout
    update("Calculating scores...")
    scorer_agent = ScorerAgent(model=model)
    msg = scorer_agent.run(msg)

    # Step 5: Explanation — short LLM call with timeout
    update("Generating feedback...")
    explanation_agent = ExplanationAgent(model=model)
    msg = explanation_agent.run(msg)

    # Step 6: Consistency check — recalculates from breakdown, no LLM
    update("Validating final score...")
    consistency_agent = ConsistencyCheckerAgent(model=model)
    msg = consistency_agent.run(msg)

    update("Evaluation complete!")
    return msg