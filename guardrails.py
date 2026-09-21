from __future__ import annotations
from typing import Any
from crewai import Agent, Task, Crew, TaskOutput
from .human_review import HumanReviewer, reviewer

def _review_with_inspector(inspector: Agent, deliverable_name: str, criteria: str, output: str) -> tuple[bool, Any]:
    review_task = Task(
        description=(
            f"Review the {deliverable_name} against the following criteria:\n\n"
            f"{criteria}\n\n"
            f"The {deliverable_name} is:\n\n"
            f"{output}\n\n"
            "Respond with exactly one word, PASS or FAIL, on the first line, and nothing "
            "else on that line. If FAIL, follow it with a clear explanation of what needs "
            "to change."
        ),
        expected_output="The single word PASS or FAIL on the first line, followed by feedback if FAIL.",
        agent=inspector,
    )
    review_crew = Crew(
        agents=[inspector],
        tasks=[review_task],
        verbose=False,
    )
    review_output = review_crew.kickoff()
    verdict = review_output.raw.strip()
    raw = review_output.raw.strip()

    first_line = raw.splitlines()[0] if raw else ""
    verdict = first_line.strip("*_:. ").upper()  # strips stray markdown/punctuation like **PASS** or PASS:

    if verdict == "PASS":
        return True, output
    return False, raw

def build_inspector_guardrail(inspector: Agent, deliverable_name: str, criteria: str):
    """
    Build a guardrail function for one specific task. CrewAI only ever
    calls a guardrail with a single argument (the TaskOutput), so this
    factory "bakes in" which agent should review, what the deliverable is
    called, and what criteria to check it against, and hands back a plain
    function matching that one-argument signature.
    """

    def guardrail(output: TaskOutput) -> tuple[bool, Any]:
        return _review_with_inspector(inspector, deliverable_name, criteria, output.raw)

    return guardrail

def build_human_review_guardrail(reviewer: HumanReviewer, deliverable_name: str):
    """
    Build a guardrail function that pauses for human approval - but only
    when station.enabled is True. When disabled, the task's output passes
    straight through and the crew is never interrupted.
    """

    def guardrail(output: TaskOutput) -> tuple[bool, Any]:
        if not reviewer.enabled:
            return True, output.raw
        approved, feedback = reviewer.request_review(deliverable_name, output.raw)
        if approved:
            return True, output.raw
        return False, feedback or "The reviewer requested changes but gave no specific feedback."

    return guardrail