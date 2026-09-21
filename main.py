from ast import Try
import sys
import warnings
from datetime import datetime
import gradio as gr
from faux_codex.crew import EngineeringTeam
from .tools.sandbox_tools import reset_sandbox
from .human_review import reviewer
from .flow import EngineeringFlow

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run_crew_with_live_updates(requirements: str):
    """
    A generator function: every `yield` immediately updates the Progress
    textbox in the Gradio UI with the value yielded, instead of waiting
    for the whole function to finish. That's what makes this "live".
    """
    if not requirements.strip():
        yield "Please describe the software you'd like built before clicking Build."
        return

    log_lines: list[str] = []

    try:
        reset_sandbox()

        flow = EngineeringFlow()
        streaming = flow.kickoff(inputs={"requirements": requirements})

        for chunk in streaming:
            if chunk.content:
                text = chunk.content
            elif chunk.tool_call:
                text = f"(using tool: {chunk.tool_call.tool_name})"
            else:
                text = ""
            log_lines.append(f"[{chunk.agent_role}] {text}")
            yield "\n".join(log_lines)

        final_result = streaming.result
        log_lines.append("\n--- DONE ---\n")
        log_lines.append(final_result.raw)
        yield "\n".join(log_lines)

    except Exception as exc:
        log_lines.append("\n--- ERROR ---\n")
        log_lines.append(str(exc))
        yield "\n".join(log_lines)

def toggle_human_review(enabled: bool) -> None:
    """Wired to the checkbox: flips the shared station's toggle on or off."""
    reviewer.enabled = enabled

def poll_human_review():
    """
    Called every second by the Timer. Shows the pending review panel and
    its contents when a task is waiting on a human decision, and hides it
    otherwise.
    """
    pending = reviewer.get_pending()
    if pending is None:
        return gr.update(visible=False), ""
    review_text = f"Reviewing {pending.deliverable_name}\n\n{pending.output}"
    return gr.update(visible=True), review_text

def approve_review():
    """Wired to the Approved button."""
    reviewer.submit_decision(approved=True)
    return gr.update(visible=False), "", ""

def send_back_review(feedback: str):
    """Wired to the Send Back button."""
    reviewer.submit_decision(approved=False, feedback=feedback)
    return gr.update(visible=False), "", ""

def build_launcher() -> gr.Blocks:
    with gr.Blocks(title="Faux Codex") as launcher:
        gr.Markdown("# Faux Codex\nA miniature analogue of OpenAI's Codex.")
        
        human_review_toggle = gr.Checkbox(
            label = "Pause for my review after each task",
            value=False,
        )
        
        requirements_input = gr.Textbox(
            label="Requirements",
            placeholder="e.g. Build a simple to-do list app with add, complete, and delete...",
            lines=8,
        )
        build_button = gr.Button("Build it", variant="primary")
        log_output = gr.Textbox(label="Progress", lines=25, interactive=False, autoscroll=True)

        with gr.Group(visible=False) as review_group:
            review_output = gr.Textbox(label="Pending Review", lines=15, interactive=False)
            feedback_input = gr.Textbox(label="Feedback (only needed if sending back)", lines=3)
            with gr.Row():
                approve_button = gr.Button("Approve", variant="primary")
                send_back_button = gr.Button("Send Back")

        review_timer = gr.Timer(1)

        human_review_toggle.change(fn=toggle_human_review, inputs=[human_review_toggle])

        build_button.click(
            fn=run_crew_with_live_updates,
            inputs=[requirements_input],
            outputs=[log_output],
        )

        review_timer.tick(
            fn=poll_human_review,
            outputs=[review_group, review_output],
        )

        approve_button.click(
            fn=approve_review,
            outputs=[review_group, review_output, feedback_input],
        )

        send_back_button.click(
            fn=send_back_review,
            inputs=[feedback_input],
            outputs=[review_group, review_output, feedback_input],
        )

    return launcher


def run():
    """
    Launch the Gradio UI. This replaces the old terminal prompt for typing
    requirements, and lets you watch the crew work in real time.
    """
    build_launcher().launch()


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        EngineeringTeam().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        EngineeringTeam().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }
    try:
        EngineeringTeam().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = EngineeringTeam().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")