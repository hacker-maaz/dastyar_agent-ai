import os
import subprocess
from pathlib import Path

from core.config import ConfigManager


class BuildVerifier:
    """
    Actually runs the project's build (and test suite) and reports
    real pass/fail — not a self-reported claim from another agent.

    Reuses the existing, already-verified scripts/build.sh and
    scripts/test.sh rather than reimplementing gradlew invocation.
    Calls no model — this is pure execution/verification.
    """

    DEFAULT_TIMEOUT = 900  # seconds — Android builds can be slow, especially cold

    def __init__(self):
        self.config = ConfigManager()

    def _project_dir(self) -> Path:
        configured = self.config.get("ACTIVE_PROJECT_PATH")
        if configured:
            return Path(os.path.expanduser(os.path.expandvars(configured)))
        return Path.home() / "ai-server" / "projects" / "k-V4"

    def _scripts_dir(self) -> Path:
        return Path.home() / "ai-server" / "scripts"

    def _run_script(self, script_name, project_dir):
        script_path = self._scripts_dir() / script_name

        try:
            result = subprocess.run(
                [str(script_path)],
                # Setting cwd here is what lets build.sh's own upward
                # search for settings.gradle.kts find the project
                # immediately, regardless of where `ai` was invoked
                # from — same fix pattern as core/execution_layer.py.
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=self.DEFAULT_TIMEOUT,
            )
            return result.returncode == 0, (result.stdout + result.stderr)

        except subprocess.TimeoutExpired:
            return False, f"{script_name} did not finish within {self.DEFAULT_TIMEOUT}s"
        except FileNotFoundError:
            return False, f"{script_name} not found at {script_path}"
        except PermissionError:
            return False, f"{script_name} is not executable (chmod +x needed)"

    def verify(self, project_dir=None) -> dict:
        project_dir = project_dir or self._project_dir()

        build_ok, build_log = self._run_script("build.sh", project_dir)

        result = {
            "build_passed": build_ok,
            "build_log_excerpt": self._tail(build_log),
            "tests_passed": None,
            "test_log_excerpt": None,
        }

        if not build_ok:
            # Don't bother running tests against a build that doesn't
            # even compile.
            return result

        tests_ok, test_log = self._run_script("test.sh", project_dir)
        result["tests_passed"] = tests_ok
        result["test_log_excerpt"] = self._tail(test_log)

        return result

    @staticmethod
    def _tail(text, max_lines=40):
        lines = text.strip().splitlines()
        if len(lines) <= max_lines:
            return "\n".join(lines)
        return "... (truncated)\n" + "\n".join(lines[-max_lines:])
