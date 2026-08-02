class BaseAgent:
    def __init__(self, name):
        self.name = name

    def run(self, command, task, context):
        raise NotImplementedError(f"{self.name} must implement run()")
