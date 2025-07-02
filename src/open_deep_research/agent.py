"""Utility functions for running the multi-agent and graph-based implementations."""

from __future__ import annotations

import asyncio

from langgraph.checkpoint.memory import MemorySaver

from .multi_agent import supervisor_builder
from .graph import graph as workflow_graph


def run_multi_agent(prompt: str, auto_accept_plan: bool = False) -> str:
    """Generate a report using the multi-agent system.

    Args:
        prompt: The human prompt or query.
        auto_accept_plan: If ``True``, skip the clarification step.

    Returns:
        The final report as a string.
    """

    async def _run() -> str:
        graph = supervisor_builder.compile(checkpointer=MemorySaver())
        config = {"configurable": {"ask_for_clarification": not auto_accept_plan}}
        await graph.ainvoke({"messages": [{"role": "user", "content": prompt}]}, config)
        state = graph.get_state(config)
        return state.values.get("final_report", "")

    return asyncio.run(_run())


def run_workflow(prompt: str, auto_accept_plan: bool = False) -> str:
    """Generate a report using the graph-based workflow.

    Args:
        prompt: The human prompt or query.
        auto_accept_plan: If ``True``, skip the human review step.

    Returns:
        The final report as a string.
    """

    async def _run() -> str:
        config = {"configurable": {"human_review": not auto_accept_plan}}
        result = await workflow_graph.ainvoke({"query": prompt}, config)
        return result.get("report", "")

    return asyncio.run(_run())
