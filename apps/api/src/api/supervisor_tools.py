from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.types import interrupt, Command

from api.calendar_agent import calendar_agent
from api.gmail_agent import gmail_agent



# Each user gets their own conversation memory, so one user's chat never
# leaks into another's.
def gmail_thread_id(user_id: str) -> str:
    return f"gmail:{user_id}"


def calendar_thread_id(user_id: str) -> str:
    return f"calendar:{user_id}"


def run_sub_agent(agent, thread_id: str, user_id: str, request: str) -> str:
    # Pass user_id down so the sub-agent's tools know whose Gmail/Calendar to use.
    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}

    # Only treat the sub-agent as "paused" if it's actually waiting on an
    # interrupt (an approval). `.next` alone can be set without one, e.g. if a
    # previous run stopped partway, and then `.interrupts` is empty.
    state = agent.get_state(config)
    pending = [i for task in state.tasks for i in task.interrupts]

    if pending:
        inner_payload = pending[0].value
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
def calendar_agent_tool(request: str, config: RunnableConfig) -> str:
    """Delegate a calendar-related request (view, create, or delete events) to the calendar specialist agent."""
    user_id = config["configurable"]["user_id"]
    return run_sub_agent(calendar_agent, calendar_thread_id(user_id), user_id, request)


@tool
def gmail_agent_tool(request: str, config: RunnableConfig) -> str:
    """Delegate an email-related request (searching, summarizing, or sending emails) to the email specialist agent."""
    # `config` is filled in by LangGraph, not by the AI model, so the model
    # can't choose (or fake) which user it acts for.
    user_id = config["configurable"]["user_id"]
    return run_sub_agent(gmail_agent, gmail_thread_id(user_id), user_id, request)
    