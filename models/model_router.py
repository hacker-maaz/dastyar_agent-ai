from core.config import ConfigManager
from models.gemini_provider_sdk import GeminiProvider


class ModelRouter:
    """
    Selects a model for the reasoning agents: Planner, Review,
    Documentation.

    Feature Agent does NOT go through here. Code execution is handled
    by core.execution_layer.OpenCodeExecutor instead — OpenCode acts,
    it doesn't just generate text for a prompt, so it doesn't belong
    in a Model Router. (models/opencode_provider.py, which wrongly
    modeled it as a BaseProvider, has been removed.)
    """

    def __init__(self):

        self.config = ConfigManager()

        self.providers = {
            "gemini": GeminiProvider(),
        }

    def current_provider(self):

        provider = self.config.get(
            "AI_PROVIDER",
            "gemini",
        )

        if provider not in self.providers:
            raise ValueError(
                f"Unknown provider: {provider}"
            )

        return self.providers[provider]

    def generate(self, prompt, agent="default"):

        if agent in ("planner", "review", "documentation"):
            provider = GeminiProvider()

        elif agent == "feature":
            raise ValueError(
                "Feature Agent no longer routes through ModelRouter. "
                "See agents/feature_agent.py and "
                "core/execution_layer.OpenCodeExecutor."
            )

        else:
            raise ValueError(f"Unknown agent: {agent}")

        return provider.generate(prompt)
