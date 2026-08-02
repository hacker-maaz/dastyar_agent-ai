from agents.planner_agent import PlannerAgent
from agents.feature_agent import FeatureAgent
from agents.review_agent import ReviewAgent
from agents.documentation_agent import DocumentationAgent


class AgentRegistry:

    @staticmethod
    def create(name):

        agents = {
            "planner": PlannerAgent,
            "feature": FeatureAgent,
            "review": ReviewAgent,
            "documentation": DocumentationAgent,
        }

        agent = agents.get(name)

        if agent is None:
            raise ValueError(f"Unknown agent: {name}")

        return agent()
