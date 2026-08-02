#!/usr/bin/env python3

import sys

from agents.planner_agent import PlannerAgent
from agents.feature_agent import FeatureAgent
from agents.build_agent import BuildAgent
from agents.review_agent import ReviewAgent
from agents.documentation_agent import DocumentationAgent
from agents.memory_manager import MemoryManager
from agents.plan_state import save_last_plan, load_last_plan
from core.project_files import read_files


class Orchestrator:
    """
    `ai plan "<task>"`     -> Planner only. Preview. If the task
                              literally names a file that exists in
                              the project, Planner sees that file's
                              real current content, not just its name.

    `ai feature "<task>"`  -> Full pipeline: Planner -> Feature ->
                              Build (real verification) -> Review ->
                              Documentation, with a bounded revision
                              loop back to Feature Agent on build
                              failure or Review rejection.

                              Review sees the EXACT files Feature
                              Agent touched (from OpenCode's own
                              reported list, not a guess), with their
                              real current content, alongside the real
                              build evidence.

    `ai feature --confirm` -> Same pipeline, reusing the exact plan
                              from the last `ai plan` instead of
                              re-planning.
    """

    ACTION_AGENTS = {
        "feature agent": ("feature", FeatureAgent),
    }

    MAX_REVISION_ATTEMPTS = 2

    def __init__(self):
        self.memory = MemoryManager()

    def _run_agent(self, name, agent, command, task, context):
        try:
            output = agent.run(command, task, context)
            return {"status": "ok", "agent": name, "output": output}
        except Exception as exc:
            return {"status": "failed", "agent": name, "reason": str(exc)}

    def _report(self, result):
        print()
        if result["status"] == "failed":
            print(f"✗ {result['agent'].title()} Agent failed: {result['reason']}")
        else:
            print(f"✓ {result['agent'].title()} Agent")
            print()
            print(result["output"])
        print()

    def _select_action_agents(self, plan_text):
        text = (plan_text or "").lower()
        selected = []
        for label, (name, agent_cls) in self.ACTION_AGENTS.items():
            if label in text:
                selected.append((name, agent_cls()))
        return selected

    def _is_approved(self, review_text):
        text = (review_text or "").upper()
        if "REJECTED" in text or "CHANGES REQUIRED" in text:
            return False
        return "APPROVED" in text

    def _base_context(self, command, task):
        # Passing task lets MemoryManager do its best-effort file
        # match (e.g. task literally names "MainActivity.kt").
        context = self.memory.load(task=task)
        context["command"] = command
        context["task"] = task
        context["previous_output"] = ""
        return context

    def _run_feature(self, command, task, context):
        """
        Runs Feature Agent and returns (result, files_touched) —
        files_touched is the exact list OpenCode reported, used to
        show Review Agent real file content, not a guess.
        """
        feature_agent = FeatureAgent()
        result = self._run_agent("feature", feature_agent, command, task, context)
        files_touched = getattr(feature_agent, "last_files_touched", None) or []
        return result, files_touched

    def run(self, command, task):

        print("=== Starting Workflow ===")
        print()
        print(f"Command : {command}")
        print(f"Task    : {task}")
        print()

        results = []

        if command == "plan":
            context = self._base_context(command, task)
            result = self._run_agent("planner", PlannerAgent(), command, task, context)
            results.append(result)
            self._report(result)

            if result["status"] == "ok":
                save_last_plan(task, result["output"])
                print("To execute exactly this plan (no re-planning), run:")
                print('  ai feature --confirm')
                print()

            print("=== Workflow Complete ===")
            return results

        if command == "review":
            context = self._base_context(command, task)
            result = self._run_agent("review", ReviewAgent(), command, task, context)
            results.append(result)
            self._report(result)
            print("=== Workflow Complete ===")
            return results

        if command == "docs":
            context = self._base_context(command, task)
            result = self._run_agent("documentation", DocumentationAgent(), command, task, context)
            results.append(result)
            self._report(result)
            print("=== Workflow Complete ===")
            return results

        if command == "feature":

            if task.strip() == "--confirm":
                saved = load_last_plan()

                if saved is None:
                    print("No previously saved plan found.")
                    print('Run `ai plan "<task>"` first, or run')
                    print('`ai feature "<task>"` directly to plan and execute in one step.')
                    print("=== Workflow Stopped ===")
                    return results

                task = saved["task"]
                plan_text = saved["plan"]

                context = self._base_context(command, task)

                print(f"Using previously approved plan for: {task}")
                plan_result = {"status": "ok", "agent": "planner", "output": plan_text}
                results.append(plan_result)
                self._report(plan_result)

            else:
                context = self._base_context(command, task)

                plan_result = self._run_agent("planner", PlannerAgent(), command, task, context)
                results.append(plan_result)

                if plan_result["status"] == "failed":
                    self._report(plan_result)
                    print("=== Workflow Stopped ===")
                    return results

                self._report(plan_result)
                plan_text = plan_result["output"]

            context["previous_output"] = plan_text

            action_agents = self._select_action_agents(plan_text)

            if not action_agents:
                print("No action agent named in the plan — stopping here.")
                print("(Planner did not mention an agent this Orchestrator")
                print(" knows how to run. Nothing was implemented.)")
                print()
                print("=== Workflow Complete (plan only) ===")
                return results

            # Today only Feature Agent is a real action agent. Run it
            # via _run_feature so we capture exactly which files it
            # touched, not a guess.
            feature_output = None
            files_touched = []

            for name, agent_cls in [(n, type(a)) for n, a in action_agents]:
                if name == "feature":
                    result, files_touched = self._run_feature(command, task, context)
                else:
                    result = self._run_agent(name, agent_cls(), command, task, context)

                results.append(result)
                self._report(result)

                if result["status"] == "failed":
                    print("=== Workflow Stopped ===")
                    return results

                context["previous_output"] = result["output"]
                feature_output = result["output"]

            approved = False

            for attempt in range(self.MAX_REVISION_ATTEMPTS + 1):

                # Give Review the EXACT files Feature Agent touched,
                # with their real current content.
                if files_touched:
                    context["relevant_file_contents"] = read_files(files_touched)

                build_result = self._run_agent("build", BuildAgent(), command, task, context)
                results.append(build_result)
                self._report(build_result)

                if build_result["status"] == "failed":
                    if attempt >= self.MAX_REVISION_ATTEMPTS:
                        print(
                            f"Build still failing after "
                            f"{self.MAX_REVISION_ATTEMPTS + 1} attempt(s). "
                            f"Stopping here for you to look at directly — "
                            f"broken work is not being documented."
                        )
                        print("=== Workflow Stopped ===")
                        return results

                    print(
                        f"Build failed (skipping Review — a non-compiling "
                        f"change can't be approved) — sending back to "
                        f"Feature Agent for revision "
                        f"{attempt + 1}/{self.MAX_REVISION_ATTEMPTS}..."
                    )

                    instructions = (
                        f"Original Plan:\n{plan_text}\n\n"
                        f"Your Previous Implementation:\n{feature_output}\n\n"
                        f"The build FAILED with this real error:\n"
                        f"{build_result['reason']}\n\n"
                        f"Please fix the build error above."
                    )
                    context["previous_output"] = instructions

                    revision_result, files_touched = self._run_feature(command, task, context)
                    results.append(revision_result)
                    self._report(revision_result)

                    if revision_result["status"] == "failed":
                        print("=== Workflow Stopped ===")
                        return results

                    feature_output = revision_result["output"]
                    context["previous_output"] = feature_output
                    continue

                build_evidence = build_result["output"]
                context["previous_output"] = (
                    f"Feature Agent's Implementation:\n{feature_output}\n\n"
                    f"Verified Build Result (actually run by the "
                    f"platform, not self-reported):\n{build_evidence}"
                )

                review_result = self._run_agent("review", ReviewAgent(), command, task, context)
                results.append(review_result)
                self._report(review_result)

                if review_result["status"] == "failed":
                    print("=== Workflow Stopped ===")
                    return results

                review_text = review_result["output"]

                if self._is_approved(review_text):
                    approved = True
                    context["previous_output"] = review_text
                    break

                if attempt >= self.MAX_REVISION_ATTEMPTS:
                    print(
                        f"Review did not approve the change after "
                        f"{self.MAX_REVISION_ATTEMPTS + 1} attempt(s). "
                        f"Stopping here for you to look at directly — "
                        f"unapproved work is not being documented."
                    )
                    print("=== Workflow Stopped ===")
                    return results

                print(
                    f"Review requested changes — sending back to Feature "
                    f"Agent for revision {attempt + 1}/{self.MAX_REVISION_ATTEMPTS}..."
                )

                instructions = (
                    f"Original Plan:\n{plan_text}\n\n"
                    f"Your Previous Implementation:\n{feature_output}\n\n"
                    f"Verified Build Result:\n{build_evidence}\n\n"
                    f"Review Feedback (revision requested):\n{review_text}\n\n"
                    f"Please revise your implementation to address the "
                    f"feedback above."
                )
                context["previous_output"] = instructions

                revision_result, files_touched = self._run_feature(command, task, context)
                results.append(revision_result)
                self._report(revision_result)

                if revision_result["status"] == "failed":
                    print("=== Workflow Stopped ===")
                    return results

                feature_output = revision_result["output"]
                context["previous_output"] = feature_output

            if not approved:
                return results

            docs_result = self._run_agent(
                "documentation", DocumentationAgent(), command, task, context
            )
            results.append(docs_result)
            self._report(docs_result)

            print("=== Workflow Complete ===")
            return results

        print(f"Unknown workflow: {command}")
        return None


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage:")
        print("python -m agents.orchestrator <command> [task]")
        sys.exit(1)

    command = sys.argv[1]
    task = " ".join(sys.argv[2:])

    Orchestrator().run(command, task)
