from __future__ import annotations
import threading
from dataclasses import dataclass

@dataclass
class ReviewRequest:
    deliverable_name: str
    output: str
    
class HumanReviewer:
    """
    Coordinates human-in-the-loop review between the crew (running on its
    own background thread, thanks to stream=True) and the Gradio UI.

    `enabled` is the toggle: while False, review requests pass straight
    through with no pause - flip it on with the Gradio checkbox to make
    the crew stop after each task and wait for a human decision.
    """

    def __init__(self) -> None:
        self.enabled: bool = False
        self._pending: ReviewRequest | None = None
        self._decision_ready = threading.Event()
        self._approved: bool = True
        self._feedback: str = ""

    def request_review(self, deliverable_name: str, output: str) -> tuple[bool, str]:
        """
        Called from the crew's background thread when a task finishes.
        Publishes the pending request for the UI to display, then blocks
        this thread until a human clicks Approve or Send Back.
        """
        self._pending = ReviewRequest(deliverable_name, output)
        self._decision_ready.clear()
        self._decision_ready.wait()
        return self._approved, self._feedback

    def get_pending(self) -> ReviewRequest | None:
        """Called from the Gradio UI's polling timer."""
        return self._pending
    
    def submit_decision(self, approved: bool, feedback: str = "") -> None:
        """Called from the Gradio UI when a human clicks Approve or Send Back."""
        self._approved = approved
        self._feedback = feedback
        self._decision_ready.set()

reviewer = HumanReviewer()