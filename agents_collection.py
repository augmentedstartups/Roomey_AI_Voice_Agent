from agents import Agent, Runner
from pydantic import BaseModel

# Basic joke agent
joker_agent = Agent(
    name="Joker",
    handoff_description="Specialist agent for joke questions",
    instructions="You are a helpful assistant with a great sense of humor.",
)

# Homework guardrail model
class HomeworkOutput(BaseModel):
    is_homework: bool
    reasoning: str


math_tutor_agent = Agent(
    name="Math Tutor",
    handoff_description="Specialist agent for math questions",
    instructions="You provide help with math problems. Explain your reasoning at each step and include examples",
)

history_tutor_agent = Agent(
    name="History Tutor",
    handoff_description="Specialist agent for historical questions",
    instructions="You provide assistance with historical queries. Explain important events and context clearly.",
)


# Triage agent with handoffs and guardrails
triage_agent = Agent(
    name="Triage Agent",
    instructions="You determine which agent to use",
    handoffs=[history_tutor_agent, math_tutor_agent, joker_agent]
)
