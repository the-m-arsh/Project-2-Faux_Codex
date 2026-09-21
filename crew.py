from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from .human_review import reviewer
from .tools.sandbox_tools import sandbox_tools
from .guardrails import build_human_review_guardrail, build_inspector_guardrail


@CrewBase
class EngineeringTeam():
    """EngineeringTeam crew"""

    agents: list[BaseAgent]
    tasks: list[Task]


    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'],
            verbose=True,
            mcps=["https://mcp.context7.com/mcp"]
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'],
            verbose=True,
            tools=sandbox_tools
        )
    
    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],
            verbose=True,
            tools=sandbox_tools,
            mcps=["https://mcp.context7.com/mcp"],
        )
    
    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'],
            verbose=True,
            tools=sandbox_tools
        )

    def project_manager(self) -> Agent:
        """
        The manager agent for the hierarchical process. 
        
        NOT decorated with @agent.
        """
        return Agent(
            config = self.agents_config['project_manager'],
            verbose = True,
        )

    def inspector(self) -> Agent:
        """
        The inspector agent, used only inside task guardrails to review
        each engineer's output before the crew moves on to the next task.

        NOT decorated with @agent.
        """
        return Agent(
            config=self.agents_config['inspector'],
            verbose=True,
        )

    @task
    def design_task(self) -> Task:
        return Task(
            config = self.tasks_config['design_task'],
            guardrails = [build_inspector_guardrail(
                self.inspector(),
                deliverable_name ="system design",
                criteria=(
                    "The design clearly lists the modules, classes, and functions to be built, "
                    "with function signatures. It assigns work to backend_engineer, "
                    "frontend_engineer, and test_engineer. It does not contain any actual code."
                    ),
                ),
                build_human_review_guardrail(reviewer, deliverable_name="system design"),
            ],
            guardrail_max_retries=3,
        )

    @task
    def code_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_task'],
            guardrails = [build_inspector_guardrail(
                self.inspector(),
                deliverable_name="backend code",
                criteria=(
                    "The backend code was written and tested using the sandbox tools, follows "
                    "the engineering lead's design, and only uses the Python standard library."
                    ),
                ),
                build_human_review_guardrail(reviewer, deliverable_name="backend code"),
            ],
            guardrail_max_retries=3,
        )

    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_task'],
            guardrails = [build_inspector_guardrail(
                self.inspector(),
                deliverable_name="gradio frontend",
                criteria=(
                    "app.py was written to the sandbox and demonstrates the backend. "
                    "_validate.py was written and run successfully, confirming the Blocks object "
                    "constructs without error, and _validate.py does not call .launch()."
                    ),
                ),
                build_human_review_guardrail(reviewer, deliverable_name="gradio frontend"),
            ],
            guardrail_max_retries=2,
        )

    @task
    def test_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_task'],
            guardrails = [build_inspector_guardrail(
                self.inspector(),
                deliverable_name="unit tests",
                criteria=(
                    "Unit tests were written for the backend module using unittest, were run "
                    "using the sandbox tools, and all tests pass."
                    ),
                ),
                build_human_review_guardrail(reviewer, deliverable_name="unit tests"),
            ],
            guardrail_max_retries=2,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the EngineeringTeam crew"""
        return Crew(
            agents=self.agents,       # engineering_lead, backend, frontend, test — NOT project_manager or inspector
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_agent=self.project_manager(),
            verbose=True,
            tracing=True,
        )