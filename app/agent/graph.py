from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import (
    fetch_emails,
    score_emails,
    filter_important,
    draft_replies,
    build_briefing,
    send_whatsapp,
    execute_action,
    update_memory,
)


def build_graph():
    graph = StateGraph(AgentState)

    # Register all nodes
    graph.add_node("fetch_emails", fetch_emails)
    graph.add_node("score_emails", score_emails)
    graph.add_node("filter_important", filter_important)
    graph.add_node("draft_replies", draft_replies)
    graph.add_node("build_briefing", build_briefing)
    graph.add_node("send_whatsapp", send_whatsapp)
    graph.add_node("execute_action", execute_action)
    graph.add_node("update_memory", update_memory)

    # Define flow
    graph.set_entry_point("fetch_emails")
    graph.add_edge("fetch_emails", "score_emails")
    graph.add_edge("score_emails", "filter_important")
    graph.add_edge("filter_important", "draft_replies")
    graph.add_edge("draft_replies", "build_briefing")
    graph.add_edge("build_briefing", "send_whatsapp")
    graph.add_edge("send_whatsapp", END)          # pauses — resumes on WhatsApp webhook

    # Approval loop (triggered by webhook)
    graph.add_edge("execute_action", "update_memory")
    graph.add_edge("update_memory", END)

    return graph.compile()


# Singleton for use across the app
agent_graph = build_graph()
