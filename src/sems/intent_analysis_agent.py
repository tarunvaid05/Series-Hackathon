"""
Intent Analysis Agent using LangGraph and Google Gemini
Analyzes iMessage text to classify user intent into 6 categories
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

load_dotenv(override=True)


# Define the structured output schema for intent classification
class IntentOutput(BaseModel):
    """Schema for intent analysis output"""
    intent: str = Field(
        description="One of: create_event, find_event, edit_event, my_events, delete_event, invite_event, no_intent"
    )
    confidence: float = Field(
        default=0.8,
        description="Confidence score from 0.0 to 1.0"
    )


class EventMatchOutput(BaseModel):
    """Schema for event matching output"""
    matching_indices: List[int] = Field(
        default_factory=list,
        description="1-based indices of events that match the query. Empty if no matches."
    )


# Define the graph state
class AgentState(TypedDict):
    """State for the intent analysis agent"""
    user_message: str
    intent: str
    confidence: float


def intent_analysis_node(state: AgentState) -> AgentState:
    """
    Analyzes user message to determine intent category

    Args:
        state: Current agent state containing user_message

    Returns:
        Updated state with intent and confidence
    """
    user_message = state["user_message"]

    # Initialize Gemini with structured output
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    # Create the structured output LLM
    structured_llm = llm.with_structured_output(IntentOutput)

    # Create the prompt - SIMPLE and FAST
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Classify the user's intent into ONE category. Be fast, not perfect.

CATEGORIES:
- create_event: User wants to CREATE/HOST/PLAN/ORGANIZE a new event or gathering
- find_event: User wants to FIND/DISCOVER/JOIN events or see what's happening
- edit_event: User wants to EDIT/CHANGE/MODIFY/UPDATE their existing event
- my_events: User wants to SEE events they're ATTENDING or SIGNED UP for
- delete_event: User wants to DELETE/REMOVE/CANCEL their own event
- invite_event: User wants to INVITE someone to an event
- no_intent: Unclear or doesn't match any category

QUICK RULES:
- Action verbs matter: create/host/plan/throw -> create_event
- Discovery words: find/discover/join/browse/what's happening -> find_event
- Modification words: edit/change/modify/update -> edit_event
- Viewing own: my events/attending/signed up for -> my_events
- Removal words: delete/remove/cancel my event -> delete_event
- Invitation words: invite/add people/send invite -> invite_event
- When unclear -> no_intent

Be decisive. Pick the most likely intent."""),
        ("human", "{message}")
    ])

    # Create the chain
    chain = prompt | structured_llm

    # Invoke the chain
    result = chain.invoke({"message": user_message})

    # Update state
    return {
        "user_message": user_message,
        "intent": result.intent,
        "confidence": result.confidence
    }


def create_intent_graph():
    """
    Creates the LangGraph workflow for intent analysis

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


def analyze_intent(message: str) -> dict:
    """
    Analyze a user message for intent classification

    Args:
        message: The user message to analyze

    Returns:
        Dictionary with intent string and confidence float
    """
    # Create the graph
    graph = create_intent_graph()

    # Run the graph
    result = graph.invoke({
        "user_message": message,
        "intent": "no_intent",  # Initial state
        "confidence": 0.0
    })

    # Return structured output
    return {
        "intent": result["intent"],
        "confidence": result["confidence"]
    }


# Backward compatibility aliases
def analyze_message(message: str) -> dict:
    """
    Legacy function for backward compatibility.
    Maps new intent system to old is_event boolean.
    """
    result = analyze_intent(message)
    return {
        "is_event": result["intent"] == "create_event",
        "intent": result["intent"],
        "confidence": result["confidence"]
    }


def create_event_intent_graph():
    """Legacy alias for create_intent_graph"""
    return create_intent_graph()


def find_matching_events(user_query: str, events: List[dict]) -> List[int]:
    """
    Use AI to match user query against event metadata.

    Args:
        user_query: What the user is looking for (e.g., "sports in brooklyn")
        events: List of event dicts with keys: title, description, location, datetime

    Returns:
        List of indices (0-based) of matching events, ordered by relevance.
        Empty list if no good matches found.
    """
    # Handle empty events list
    if not events:
        return []

    # Build numbered event list for prompt (title, location, datetime only)
    event_lines = []
    for i, event in enumerate(events, start=1):
        title = event.get("title", "Untitled")
        location = event.get("location", "Unknown location")
        datetime_str = event.get("datetime", "TBD")
        event_lines.append(f"{i}. {title} - {location} - {datetime_str}")

    events_text = "\n".join(event_lines)

    # Initialize Gemini with structured output
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    structured_llm = llm.with_structured_output(EventMatchOutput)

    # Create the prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an event matching assistant. Given a user query and a list of events, identify which events semantically match what the user is looking for.

Consider:
- Location matches (city, neighborhood, venue)
- Activity type matches (sports, arts, social, etc.)
- General theme or interest alignment

Be generous with matches - it's better to suggest something potentially relevant than miss a good match.
Only return empty if there's truly no reasonable connection.

Return the 1-based indices of matching events, ordered by relevance (best match first)."""),
        ("human", """User is looking for: "{query}"

Available events:
{events}

Which events match what the user is looking for?""")
    ])

    # Create and invoke the chain
    chain = prompt | structured_llm

    try:
        result = chain.invoke({"query": user_query, "events": events_text})

        # Convert 1-based indices to 0-based, filter out invalid indices
        zero_based = []
        for idx in result.matching_indices:
            zero_idx = idx - 1
            if 0 <= zero_idx < len(events):
                zero_based.append(zero_idx)

        return zero_based
    except Exception as e:
        print(f"Error in find_matching_events: {e}")
        return []


# Example usage and testing
if __name__ == "__main__":
    test_messages = [
        # create_event
        ("I want to create an event", "create_event"),
        ("Let's host a party this weekend", "create_event"),
        ("I'm organizing a soccer game at Battery Park", "create_event"),
        ("Planning a book club meetup next Thursday", "create_event"),
        ("I want to throw a birthday party", "create_event"),

        # find_event
        ("What events are happening this weekend?", "find_event"),
        ("I want to find events near me", "find_event"),
        ("Are there any parties I can join?", "find_event"),
        ("What's going on tonight?", "find_event"),
        ("Show me upcoming events", "find_event"),
        ("I want to discover new events", "find_event"),

        # edit_event
        ("I need to edit my event", "edit_event"),
        ("Can I change the time of my event?", "edit_event"),
        ("Update my event description", "edit_event"),
        ("Modify the location of my party", "edit_event"),

        # my_events
        ("Show me my events", "my_events"),
        ("What events am I attending?", "my_events"),
        ("What have I signed up for?", "my_events"),
        ("List my upcoming events", "my_events"),

        # delete_event
        ("Delete my event", "delete_event"),
        ("I want to cancel my party", "delete_event"),
        ("Remove my event listing", "delete_event"),

        # no_intent
        ("Hello", "no_intent"),
        ("What's the weather like?", "no_intent"),
        ("I'm going to the gym later", "no_intent"),
        ("Thanks for your help", "no_intent"),
        ("Anyone selling concert tickets?", "no_intent"),
    ]

    print("Intent Analysis Results:")
    print("=" * 70)

    correct = 0
    total = len(test_messages)

    for message, expected in test_messages:
        result = analyze_intent(message)
        match = result["intent"] == expected
        if match:
            correct += 1

        status = "[OK]" if match else "[FAIL]"
        print(f"\n{status} Message: {message}")
        print(f"   Expected: {expected}")
        print(f"   Got: {result['intent']} (confidence: {result['confidence']:.2f})")

    print("\n" + "=" * 70)
    print(f"Accuracy: {correct}/{total} ({100*correct/total:.1f}%)")

    # Test find_matching_events function
    print("\n\nEvent Matching Results:")
    print("=" * 60)

    # Sample events for testing
    test_events = [
        {"title": "Soccer Game", "location": "Battery Park", "datetime": "Saturday 3pm"},
        {"title": "Book Club Meeting", "location": "Manhattan Library", "datetime": "Friday 7pm"},
        {"title": "Yoga Session", "location": "Central Park", "datetime": "Sunday 9am"},
        {"title": "Basketball Pickup", "location": "Brooklyn Courts", "datetime": "Saturday 2pm"},
        {"title": "Art Gallery Opening", "location": "SoHo Gallery", "datetime": "Thursday 6pm"},
        {"title": "Tech Networking Mixer", "location": "WeWork Manhattan", "datetime": "Wednesday 7pm"},
    ]

    test_queries = [
        "things to do in Battery Park",
        "sports to play in New York",
        "activities in Brooklyn",
        "something artsy to do",
        "where can I meet people in tech",
        "yoga or meditation classes",
        "random stuff in Chicago",  # Should return empty - no Chicago events
    ]

    print("\nAvailable events:")
    for i, event in enumerate(test_events):
        print(f"  {i}: {event['title']} - {event['location']} - {event['datetime']}")
    print()

    for query in test_queries:
        matches = find_matching_events(query, test_events)
        print(f"\nQuery: \"{query}\"")
        if matches:
            print(f"  Matches (0-based indices): {matches}")
            for idx in matches:
                print(f"    -> {test_events[idx]['title']} at {test_events[idx]['location']}")
        else:
            print("  No matches found")

    # Test edge cases
    print("\n\nEdge Case Tests:")
    print("-" * 40)

    # Empty events list
    empty_result = find_matching_events("sports", [])
    print(f"Empty events list: {empty_result} (expected: [])")

    # Events with missing fields
    partial_events = [
        {"title": "Mystery Event"},  # Missing location and datetime
        {"location": "Some Place"},  # Missing title and datetime
    ]
    partial_result = find_matching_events("mystery", partial_events)
    print(f"Partial event data: {partial_result}")

    print("\n" + "=" * 60)
