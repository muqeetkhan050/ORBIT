from langchain_core.tools import tool
from langgraph.types import interrupt, Command

from api.calendar_agent import calendar_agent
from api.gmail_agent import gmail_agent



def run_sub_agent(agent, thread_id: str, request: str) -> str:
    config = {"configurable": {"thread_id": thread_id}}

    if agent.get_state(config).next:
        inner_payload = agent.get_state(config).tasks[0].interrupts[0].value
    else:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": request}]},
            config=config,
        )
        if "__interrupt__" not in result:
            return result["messages"][-1].content
        inner_payload = result["__interrupt__"][0].value

    decision = interrupt(inner_payload)
    result = agent.invoke(Command(resume=decision), config=config)
    return result["messages"][-1].content


@tool
def calendar_agent_tool(request: str) -> str:
    """Delegate a calendar-related request (view, create, or delete events) to the calendar specialist agent."""
    return run_sub_agent(calendar_agent, "supervisor-calendar-thread", request)


@tool
def gmail_agent_tool(request: str) -> str:
    """Delegate an email-related request (searching, summarizing, or sending emails) to the email specialist agent."""
    return run_sub_agent(gmail_agent, "supervisor-gmail-threadd", request)
    