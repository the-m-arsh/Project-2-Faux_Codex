from __future__ import annotations
from pydantic import BaseModel
from crewai.flow.flow import Flow, start
from .crew import EngineeringTeam

class EngineeringFlowState(BaseModel):
    """
    Holds the one piece of data this flow needs: the requirements typed
    into the Gradio UI. Flow state must be a Pydantic model (or left as
    the default dict) - this just defines its shape.
    """
    requirements: str = ""

class EngineeringFlow(Flow[EngineeringFlowState]):
    """
    Wraps the EngineeringTeam crew as a single Flow step. This doesn't
    change what the crew does - it's still the same hierarchical crew,
    with the same inspector and human-review guardrails - it just runs
    inside a Flow, which is the shape CrewAI expects if you want to add
    steps before or after it later (e.g. a validation step before
    building, or a notification step once it's done).

    stream = True makes flow.kickoff() return a streaming object you can
    iterate for live chunks, the same way Crew(stream=True) did - CrewAI
    forwards streaming from any crew run inside the flow automatically.
    """

    stream = True

    @start()
    def build_software(self):
        crew = EngineeringTeam().crew()
        return crew.kickoff(inputs={"requirements": self.state.requirements})