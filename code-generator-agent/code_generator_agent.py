from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import os

import io
import contextlib

# Setting up LangSmith connection.
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "enter your langsmith api key"
os.environ["LANGSMITH_PROJECT"] = "dynamic-group-chat"

# Setting up ChatGPT connection
llm = ChatOpenAI(model="gpt-4o-mini", api_key= "enter your openai api key")

# Safety cap so the agents cannot loop forever if the manager never terminates.
MAX_TURNS = 15

# Shared state.
class GroupChatState(TypedDict):
    task : str
    conversation_history : Annotated[list, add_messages]
    next_speaker : str
    turn_count : int

# Kicks off the chat by posting the user's task as the first message.
def admin_node(state: GroupChatState):
    user_task = {"role" : "user" , "content" : state["task"]} 
    return {"conversation_history" : [user_task]}

# Decides who speaks next (Engineer, Critic, Executor) or ends the chat.
def manager_node(state: GroupChatState):
    prompt = """
            You are the manager of a group chat. Your job is to decide which agent in the group chat should speak next based on the conversation history and the task at hand. 

            Here are the agents you have at your disposal:

            1) Engineer: This agent is skilled at producing optimal code to solve any task it is given.
            2) Critic: This agent is skilled at analyzing the code and providing constructive feedback on how to improve it if needed.
            3) Executor: This agent is skilled at executing the code and providing the output.

            After you have made your decision, respond with only ONE word indicating the next speaker: "Engineer", "Critic", or "Executor".

            Additionally, if the task has been completed already. Respond with the word "TERMINATE".
    """
    response = llm.invoke([{"role" : "system" , "content" : prompt}] + state["conversation_history"])
    print(f"\nManager selected: {response.content.strip()}")
    return {"next_speaker" : response.content.strip() , "turn_count" : state["turn_count"] + 1}

# Writes (or revises) the Python code that solves the task.
def engineer_node(state: GroupChatState):
    prompt = """
            You are an Engineer in a group chat. Your job is to write Python code to solve the task given.
            Follow these rules:
        
            1) Briefly explain your approach before providing the code.
            2) Always wrap your code in a ```python code block.
            3) Only use Python built-in libraries. Do not import numpy, scipy, or any external package.
            4) If you see feedback from the Critic or errors from the Executor in the conversation history, 
            revise your code accordingly and explain what you changed.
            5) The code must be complete and runnable as-is.
            """
    
    response = llm.invoke([{"role" : "system" , "content" : prompt}] + state["conversation_history"])
    print(f"\nEngineer response: {response.content}")
    return {"conversation_history" : [response]}

# Reviews the Engineer's code and gives feedback, without rewriting it.
def critic_node(state: GroupChatState):
    prompt = """
            You are a Critic in a group chat. Your job is to review the Python code written by the Engineer.
            Follow these rules:

            1) Carefully review the code for any bugs, errors, or logical issues.
            2) If you find issues, provide clear and constructive feedback explaining what is wrong and how to fix it.
            3) If the code looks correct and complete, explicitly say so — for example: "The code looks correct and is ready to be executed."
            4) Do not rewrite the code yourself — that is the Engineer's job.
            5) Keep your feedback concise and focused.
            """
    
    response = llm.invoke([{"role" : "system" , "content" : prompt}] + state["conversation_history"])
    print(f"\nCritic response: {response.content}")
    return {"conversation_history" : [response]}

# Runs the latest code block from the chat and reports its output or error.
def executor_node(state: GroupChatState):
    code = ""
    for message in reversed(state["conversation_history"]):
        if hasattr(message, "content"):
            content = message.content
        else:
            content = str(message)

        if "```python" in content:
            start = content.find("```python") + len("```python")
            end = content.find("```", start)
            if end != -1:
                code = content[start:end].strip()
            break

    # Nothing to run: tell the group so the manager can send it back to the Engineer.
    if not code:
        return {"conversation_history" : [{"role" : "user" , "content" : "Executor: no Python code found to execute."}]}

    # Capture anything the code prints so it can be shared with the group.    
    buffer = io.StringIO()
    local_variables = {}

    try:
        with contextlib.redirect_stdout(buffer):
            exec(code, {}, local_variables)
        output = buffer.getvalue()
        if not output:
            output = "Code executed successfully with no output."
        
        result_message = f"Executor Output:\n{output}"

    except Exception as e:
        result_message = f"Execution Error: {str(e)}"

    print(f"\nExecutor response: {result_message}")
    return {"conversation_history" : [{"role" : "user" , "content" : result_message}]}

# Turns the manager's decision into the name of the graph branch to take next.
def route_node(state: GroupChatState):
    if state["turn_count"] >= MAX_TURNS:
        return "END"
    elif "TERMINATE" in state["next_speaker"]:
        return "END"
    elif "Engineer" in state["next_speaker"]:
        return "Engineer"
    elif "Critic" in state["next_speaker"]:
        return "Critic"
    elif "Executor" in state["next_speaker"]:
        return "Executor"
    else:
        return "END"
    
# Creating graph.
graph = StateGraph(GroupChatState)

graph.add_node(admin_node)
graph.add_node(manager_node)
graph.add_node(engineer_node)
graph.add_node(critic_node)
graph.add_node(executor_node)

graph.set_entry_point("admin_node")

graph.add_edge("admin_node" , "manager_node")
graph.add_edge("engineer_node", "manager_node")
graph.add_edge("critic_node", "manager_node")
graph.add_edge("executor_node", "manager_node")

graph.add_conditional_edges("manager_node" , route_node, {
    "Engineer" : "engineer_node",
    "Critic" : "critic_node",
    "Executor" : "executor_node",
    "END" : END
    })

app = graph.compile()

def runner(task : str):
    initial_state = {
        "task" : task,
        "conversation_history" : [],
        "next_speaker" : "",
        "turn_count" : 0,
    }

    print("--- Starting Group Chat ---")
    final_answer = app.invoke(initial_state)
    print("\n--- Group Chat Complete ---")


runner("Write a Python program that takes the list of numbers [4, 7, 13, 2, 7, 9, 1, 7, 3, 15] and calculates the mean, median, mode, and standard deviation. Print each result clearly labeled.")