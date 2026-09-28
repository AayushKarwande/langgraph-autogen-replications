from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import os

# Setting up LangSmith connection.
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "enter your langsmith api key"
os.environ["LANGSMITH_PROJECT"] = "math-agent"

# Setting up ChatGPT connection.
llm = ChatOpenAI(model="gpt-4o-mini", api_key= "enter your openai api key")

# Setting up state.
class MathState(TypedDict):
    question : str
    student_conversation_history : Annotated[list, add_messages]
    expert_conversation_history : Annotated[list, add_messages]

# UserProxyAgent node -> Communicator between student agent AND student.
def student_proxy_agent(state: MathState):
    if len(state["student_conversation_history"]) == 0:
        user_question = {"role" : "user" , "content" : state["question"]} 
        return {"student_conversation_history" : [user_question]}
    else:
        recent_message = state["student_conversation_history"][-1].content
        print(f"Most recent LLM response: {recent_message}")
        user_input = input("Student: ")
        return {"student_conversation_history" : [{"role" : "user" , "content" : user_input}]}
    
# AssistantAgent node -> Communicator with LLM to solve math problem.
def student_assistant_agent(state: MathState):
    prompt = """
            You are being used in a multi-agent system model. You need to follow these rules:

            1) If you are presented only with a mathematics question, solve it and return an answer to it.
            2) If the student expresses dissatisfaction with your answer, or if you are uncertain about your solution, respond with NEED EXPERT: <description> where description summarizes the problem, what you have tried, and what you need help with.
            3) Only respond with FINAL ANSWER: <answer> after the student has explicitly confirmed your answer is correct.
            4) Always respond in plain text only. Do not use LaTeX, markdown, special symbols, or any formatting. Write all equations and math in plain readable text.
            5) If you receive a message with expert guidance, use that guidance to 
               reformulate your answer and present the updated solution to the student, then 
               ask them to confirm if it is correct.
    """

    response = llm.invoke([{"role" : "system" , "content" : prompt}] + state["student_conversation_history"])
    return {"student_conversation_history" : [response]}

# Route node -> Directs whether to terminate or route to expert.
def student_route_agent(state: MathState):
    recent_message = state["student_conversation_history"][-1].content
    if "FINAL ANSWER" in recent_message:
        return "END"
    elif "NEED EXPERT" in recent_message:
        return "expert_proxy_agent"
    else:
        return "student_proxy_agent"
    
# Communicator between the expert assistant AND the human expert typing at the terminal.
def expert_proxy_agent(state: MathState):
    if len(state["expert_conversation_history"]) == 0:
        need_expert_message = state["student_conversation_history"][-1].content
        print(f"Expert needed: {need_expert_message}")
        expert_input = input("Expert: ")
        return {"expert_conversation_history" : [{"role" : "user" , "content" : expert_input}]}
    else:
        recent_message = state["expert_conversation_history"][-1].content
        print(f"Most recent expert assistant response: {recent_message}")
        expert_input = input("Expert: ")
        return {"expert_conversation_history" : [{"role" : "user" , "content" : expert_input}]}

# Turns the expert's raw input into guidance, and hands it to the student once confirmed.  
def expert_assistant_agent(state: MathState):
    prompt = """
        You are being used in a multi-agent system model. You are an expert math assistant 
        helping an expert human provide guidance to a struggling student assistant. Follow these rules:

        1) Take the expert's input and formulate a clear, well-structured response that can help the student assistant solve the problem.
        2) Always respond in plain text only. Do not use LaTeX, markdown, special symbols, or any formatting.
        3) Only respond with EXPERT DONE: <response> after the expert has explicitly confirmed your answer is correct, where response is the guidance to send back to the student assistant.
        4) If the expert's input is not sufficient to formulate a complete response, ask the 
           expert for more information without using EXPERT DONE.  
        5) On your first response, never use EXPERT DONE. Always present your formulated response and ask the expert to confirm it is accurate before sending. 
    """

    response = llm.invoke([{"role" : "system" , "content" : prompt}] + state["expert_conversation_history"])

    if "EXPERT DONE" in response.content:
        expert_response = response.content.split("EXPERT DONE: ")[1].strip()
        return {
            "expert_conversation_history" : [response],
            "student_conversation_history" : [{"role" : "user" , "content" : f"Expert guidance: {expert_response}"}]
        }
    else:
        return {"expert_conversation_history" : [response]}
    

# Route node -> Directs whether to return to student assistant or loop back to expert proxy agent.
def expert_route_agent(state: MathState):
    recent_message = state["expert_conversation_history"][-1].content

    if "EXPERT DONE" in recent_message:
        return "student_assistant_agent"
    else:
        return "expert_proxy_agent"
    
# Creating graph.
graph = StateGraph(MathState)
graph.add_node(student_proxy_agent)
graph.add_node(student_assistant_agent)
graph.add_node(expert_proxy_agent)
graph.add_node(expert_assistant_agent)

graph.set_entry_point("student_proxy_agent")
graph.add_edge("student_proxy_agent" , "student_assistant_agent")
graph.add_edge("expert_proxy_agent" , "expert_assistant_agent")

graph.add_conditional_edges("student_assistant_agent" , student_route_agent, {
    "student_proxy_agent" : "student_proxy_agent",
    "expert_proxy_agent" : "expert_proxy_agent",
    "END" : END
    })

graph.add_conditional_edges("expert_assistant_agent", expert_route_agent, {
    "student_assistant_agent" : "student_assistant_agent",
    "expert_proxy_agent" : "expert_proxy_agent"
})

app = graph.compile()

def runner(question : str):
    initial_state = {
        "question" : question,
        "student_conversation_history" : [],
        "expert_conversation_history" : []
    }

    final_answer = app.invoke(initial_state)
    print(final_answer["student_conversation_history"][-1].content)

runner("A uniform ladder of length 5 m and mass 20 kg leans against a frictionless wall at an angle of 60 degrees to the horizontal. The coefficient of static friction between the ladder and the floor is 0.3. How far up the ladder can a 70 kg person climb before the ladder begins to slip?")