from models.base_provider import BaseProvider


class OpenCodeProvider(BaseProvider):

    def generate(self, prompt: str) -> str:
        raise NotImplementedError(
            "OpenCode provider not implemented yet."
        )
