from langchain_core.tools import tool
from langgraph.types import interrupt, Command

from api.calendar_agent import calendar_agent
from api.gmail_agent import gmail_agent


@tool
def calendar_agent_tool(request: str) -> str:
    """Delegate a calendar-related request (view, create, or delete events) to the calendar specialist agent."""
    config = {"configurable": {"thread_id": "supervisor-calendar-thread"}}

    pending = calendar_agent.get_state(config).next

    if pending:
        state = calendar_agent.get_state(config)
        inner_payload = state.tasks[0].interrupts[0].value
    else:
        result = calendar_agent.invoke(
            {"messages": [{"role": "user", "content": request}]},
            config=config,
        )
        if "__interrupt__" not in result:
            return result["messages"][-1].content
        inner_payload = result["__interrupt__"][0].value

    decision = interrupt(inner_payload)
    result = calendar_agent.invoke(Command(resume=decision), config=config)
    return result["messages"][-1].content


@tool
def gmail_agent_tool(request: str) -> str:
    """Delegate an email-related request (searching or summarizing the inbox) to the email specialist agent."""
    result = gmail_agent.invoke(
        {"messages": [{"role": "user", "content": request}]},
        config={"configurable": {"thread_id": "supervisor-gmail-thread"}},
    )
    return result["messages"][-1].content
