"""Tiny 2-node LangGraph practice flow with conditional edge."""

from typing import TypedDict

from langgraph.graph import END, StateGraph


class MiniState(TypedDict):
    user_input: str
    processed_output: str
    should_end: bool


def process_node(state: MiniState) -> MiniState:
    output = state["user_input"].strip().upper()
    return {
        **state,
        "processed_output": output,
        "should_end": len(output) >= 3,
    }


def output_node(state: MiniState) -> MiniState:
    print(f"Output: {state['processed_output']}")
    return state


def route_after_process(state: MiniState) -> str:
    return "output" if state["should_end"] else END


def build_graph():
    graph = StateGraph(MiniState)
    graph.add_node("process", process_node)
    graph.add_node("output", output_node)
    graph.set_entry_point("process")
    graph.add_conditional_edges("process", route_after_process, {"output": "output", END: END})
    graph.add_edge("output", END)
    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    short_run = app.invoke({"user_input": "hi", "processed_output": "", "should_end": False})
    print(f"Short run finished. should_end={short_run['should_end']}")

    long_run = app.invoke({"user_input": "stripe", "processed_output": "", "should_end": False})
    print(f"Long run finished. should_end={long_run['should_end']}")
