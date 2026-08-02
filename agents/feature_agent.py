from agents.base_agent import BaseAgent
from core.execution_layer import OpenCodeExecutor


class FeatureAgent(BaseAgent):

    def __init__(self):
        self.executor = OpenCodeExecutor()
        # Set after run() completes — the Orchestrator reads this
        # directly to know exactly which files to show Review Agent,
        # rather than guessing.
        self.last_files_touched = []

    def run(self, command, task, context):

        plan = context.get("previous_output", "") or task

        result = self.executor.execute(task=plan)

        self.last_files_touched = result["files_touched"]

        if result["status"] == "failed":
            raise RuntimeError(result["reason"])

        files = ", ".join(result["files_touched"]) or "(none reported)"

        return (
            f"Summary\n{result['summary']}\n\n"
            f"Files Changed\n- {files}"
        )
