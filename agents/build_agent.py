from agents.base_agent import BaseAgent
from core.build_verifier import BuildVerifier


class BuildAgent(BaseAgent):
    """
    Runs the ACTUAL build (and test suite) against the project and
    reports real, verified pass/fail — not a self-reported claim from
    Feature Agent. Review Agent's verdict is now grounded in this
    output, instead of trusting Feature Agent's own summary of its
    own work.

    Calls no model — this is pure execution/verification, consistent
    with "models think, frameworks act."
    """

    def __init__(self):
        self.verifier = BuildVerifier()

    def run(self, command, task, context):

        result = self.verifier.verify()

        if not result["build_passed"]:
            raise RuntimeError(
                "Build FAILED:\n" + result["build_log_excerpt"]
            )

        lines = [
            "Build Verification (actually run, not self-reported)",
            "",
            "Build: PASSED",
            "",
            "Build Output:",
            result["build_log_excerpt"],
        ]

        if result["tests_passed"] is False:
            lines.append("")
            lines.append("Tests: FAILED")
            lines.append("")
            lines.append("Test Output:")
            lines.append(result["test_log_excerpt"])
            raise RuntimeError("\n".join(lines))

        if result["tests_passed"] is True:
            lines.append("")
            lines.append("Tests: PASSED")
            lines.append("")
            lines.append("Test Output:")
            lines.append(result["test_log_excerpt"])

        return "\n".join(lines)
