from agents import Agent, Runner,WebSearchTool, trace
from pydantic import BaseModel
from tools import get_stock_price


web_search_agent = Agent(
    name="Web searcher",
    instructions="You are a helpful agent. that can search the web for information. Keep information conversational and max two paragraphs.",
    tools=[WebSearchTool(search_context_size="low")],
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

stock_price_agent = Agent(
    name='stock_agent',
    instructions= 'You are an agent who retrieves stock prices. If a ticker symbol is provided, fetch the current price. If only a company name is given, first perform a Google search to find the correct ticker symbol before retrieving the stock price. If the provided ticker symbol is invalid or data cannot be retrieved, inform the user that the stock price could not be found.',
    handoff_description='This agent specializes in retrieving real-time stock prices within 2 decimal places. Given a stock ticker symbol (e.g., AAPL, GOOG, MSFT) or the stock name, use the tools and reliable data sources to provide the most up-to-date price.',
    tools=[get_stock_price]
)


# Triage agent with handoffs and guardrails
triage_agent = Agent(
    name="Triage Agent",
    instructions="You determine which agent to use",
    handoffs=[history_tutor_agent, math_tutor_agent,stock_price_agent,web_search_agent]
)
