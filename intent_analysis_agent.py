"""
Event Intent Analysis Agent using LangGraph and Google Gemini 2.5 Pro
Analyzes iMessage text to determine if user wants to create an event
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Define the structured output schema
class EventIntentOutput(BaseModel):
    """Schema for event intent analysis output"""
    is_event: bool = Field(
        description="True if the message indicates intent to create an event, False otherwise"
    )


# Define the graph state
class AgentState(TypedDict):
    """State for the intent analysis agent"""
    user_message: str
    is_event: bool


def intent_analysis_node(state: AgentState) -> AgentState:
    """
    Analyzes user message to determine event creation intent
    
    Args:
        state: Current agent state containing user_message
        
    Returns:
        Updated state with is_event determination
    """
    user_message = state["user_message"]
    
    # Initialize Gemini 2.5 Pro with structured output
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # Create the structured output LLM
    structured_llm = llm.with_structured_output(EventIntentOutput)
    
    # Create the prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert intent classifier for an event planning assistant.

Your task: Determine if the user wants to CREATE a new event.

DEFINITION OF AN EVENT:
An event is a planned gathering or activity involving 5 OR MORE people that requires coordination and organization.

THREE CRITERIA FOR EVENT CREATION INTENT (all must be true):

1. GROUP SIZE: The activity must involve 5+ people
   - Indicators of 5+: "party", "team", "tournament", "celebration", "everyone", "the group", "public event"
   - Indicators of <5: specific names mentioned ("with Sarah and John"), "my friend", "my roommate", "a couple friends"
   - If unclear, use activity context (soccer = team sport = 5+, coffee = usually 2 people)

2. CREATION INTENT: User wants to START planning/organizing something new
   - Look for: action verbs (plan, host, organize, throw, arrange) + desire expressions ("I want to", "I'd like to")
   - Focus must be on THE EVENT ITSELF, not a component of it
   
3. NOT A LOGISTICS REQUEST: User is not asking for help with an existing event
   - Red flags: transitional phrases ("but I need", "however", "looking for"), vendor/service requests ("need a photographer", "recommendations for"), supply questions ("where can I find")
   - If there's a compound statement, the ACTUAL REQUEST (typically after transitional phrases) determines classification

CLASSIFICATION LOGIC:
- If group size < 5 people → FALSE (small gathering)
- If asking for vendors/recommendations/supplies → FALSE (logistics request)
- If event already exists and asking for help → FALSE (logistics request)
- If asking about events, not creating → FALSE (inquiry)
- If wanting to create a new activity with 5+ people → TRUE (event creation)

Examples for calibration:
TRUE: "I'm hosting a party", "I want to organize a team outing", "Let's plan a soccer tournament"
FALSE: "I want to grab coffee with my friend" (2 people), "I'm having a wedding, but I need a photographer" (logistics), "What events are happening?" (inquiry)

Respond with ONLY the structured output indicating whether this is event creation intent."""),
        ("human", "User message: {message}")
    ])
    
    # Create the chain
    chain = prompt | structured_llm
    
    # Invoke the chain
    result = chain.invoke({"message": user_message})
    
    # Update state
    return {
        "user_message": user_message,
        "is_event": result.is_event
    }


def create_event_intent_graph():
    """
    Creates the LangGraph workflow for event intent analysis
    
    Returns:
        Compiled LangGraph workflow
    """
    # Initialize the graph
    workflow = StateGraph(AgentState)
    
    # Add the single intent analysis node
    workflow.add_node("intent_analysis", intent_analysis_node)
    
    # Set entry point
    workflow.set_entry_point("intent_analysis")
    
    # Add edge to END
    workflow.add_edge("intent_analysis", END)
    
    # Compile the graph
    return workflow.compile()


def analyze_message(message: str) -> dict:
    """
    Analyze a user message for event creation intent
    
    Args:
        message: The user message to analyze
        
    Returns:
        Dictionary with is_event boolean
    """
    # Create the graph
    graph = create_event_intent_graph()
    
    # Run the graph
    result = graph.invoke({
        "user_message": message,
        "is_event": False  # Initial state
    })
    
    # Return structured output
    return {
        "is_event": result["is_event"]
    }


# Example usage and testing
if __name__ == "__main__":
    # Make sure to set your GOOGLE_API_KEY environment variable
    # export GOOGLE_API_KEY="your-api-key-here"

    test_messages = [
      # Explicit event language
      "I want to create an event",
      "Let's host a party this weekend",
      "I'm organizing a soccer game at Battery Park",
      "Planning a book club meetup next Thursday",

      # Group activities with open invitation
      "Free yoga session in Central Park - all levels welcome",
      "Pickup basketball at the courts, need players",
      "Community cleanup day at Prospect Park",
      "Open mic night at my place",

      # Structured gatherings
      "Workshop on pottery making - 20 spots available",
      "Networking event for tech folks",
      "Study group for the bar exam",

      # Capacity/signup implied
      "Hiking trip to Bear Mountain - limited to 15 people",
      "Rooftop BBQ, RSVP so I know how much food to get",
      "Trivia night, forming teams of 4",

      # 1-on-1 or small friend group (2-3 people)
      "I'm going to a bar and would love to have a few friends",
      "Anyone want to grab coffee tomorrow?",
      "Who wants to get dinner tonight?",
      "Hitting up happy hour after work, join me",

      # Personal plans (not organizing)
      "I'm going to the gym later",
      "Thinking about checking out that new restaurant",
      "Might go to the beach this weekend",
      "I have a doctor's appointment",

      # Vague/no commitment
      "We should hang out sometime",
      "Would be fun to do something soon",


      # Asking for recommendations (not hosting)
      "What's a good bar around here?",
      "Any restaurant suggestions?",

      # Existing plans with set group
      "Meeting up with John and Sarah later",
      "Catching up with my college roommate",

      # Professional/transactional
      "Anyone selling concert tickets?",
      "Looking for a dog walker",

      # Small but could scale
      "Watching the game at my place"
      "Watching the Super Bowl at my place - open invite"

      # Birthday/celebration
      "It's my birthday next week"
      "Birthday party next Saturday!"

      # Recurring vs one-time
      "I run every morning in the park",
      "Morning run club - meet at 7am",

      # Size ambiguity
      "Brunch this Sunday",
      "Brunch party this Sunday",

      # Interest gauging
      "Would anyone be interested in a hiking group?",
      "Starting a hiking group - first hike Saturday",
  ]
    

    
    print("Event Intent Analysis Results:")
    print("=" * 60)
    
    for message in test_messages:
        result = analyze_message(message)
        emoji = "📅" if result["is_event"] else "💬"
        print(f"\n{emoji} Message: {message}")
        print(f"   Is Event: {result['is_event']}")
    
    print("\n" + "=" * 60)