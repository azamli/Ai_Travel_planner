# # # import os
# # # from typing import TypedDict, Annotated
# # # import operator
# # #
# # # from langgraph.graph import StateGraph, START, END
# # # from langgraph.checkpoint.memory import MemorySaver
# # # from langchain_core.messages import (
# # #     AnyMessage,
# # #     HumanMessage,
# # #     AIMessage,
# # #     SystemMessage,
# # # )
# # #
# # # from langchain_groq import ChatGroq
# # #
# # # from tavily_tool import tavily_search
# # # from flight_tool import search_flights
# # # from dotenv import load_dotenv
# # #
# # # load_dotenv()
# # #
# # # DATABASE_URL = os.getenv("DATABASE_URL")
# # #
# # # # LLM
# # # llm = ChatGroq(model="llama-3.3-70b-versatile")
# # #
# # #
# # # # ---------------- State ----------------
# # # class TravelState(TypedDict):
# # #     messages: Annotated[list[AnyMessage], operator.add]
# # #     user_query: str
# # #     flight_results: str
# # #     hotel_results: str
# # #     itinerary: str
# # #     llm_calls: int
# # #
# # #
# # # # ---------------- Flight Agent ----------------
# # # def flight_agent(state: TravelState):
# # #     query = state["user_query"]
# # #     flight_data = search_flights(query)
# # #     return {
# # #         "flight_results": flight_data,
# # #         "messages": [AIMessage(content="Flight results fetched")],
# # #         "llm_calls": state.get("llm_calls", 0) + 1,
# # #     }
# # #
# # #
# # # # ---------------- Hotel Agent ----------------
# # # def hotel_agent(state: TravelState):
# # #     query = f"Best hotels for {state['user_query']}"
# # #     hotel_results = tavily_search(query)
# # #     return {
# # #         "hotel_results": hotel_results,
# # #         "messages": [AIMessage(content="Hotel information fetched")],
# # #         "llm_calls": state.get("llm_calls", 0) + 1,
# # #     }
# # #
# # #
# # # # ---------------- Itinerary Agent ----------------
# # # def itinerary_agent(state: TravelState):
# # #     prompt = f"""
# # #     Create a travel itinerary.
# # #     User Query:
# # #     {state['user_query']}
# # #
# # #     Flight Results:
# # #     {state['flight_results']}
# # #
# # #     Hotel Results:
# # #     {state['hotel_results']}
# # #     """
# # #
# # #     response = llm.invoke([
# # #         SystemMessage(content="You are an expert travel planner. Create a clear, "
# # #                               "day-wise itinerary with approximate costs where possible."),
# # #         HumanMessage(content=prompt),
# # #     ])
# # #
# # #     return {
# # #         "itinerary": response.content,
# # #         "messages": [response],
# # #         "llm_calls": state.get("llm_calls", 0) + 1,
# # #     }
# # #
# # #
# # # # ---------------- Final Response Agent ----------------
# # # def final_agent(state: TravelState):
# # #     final_prompt = f"""
# # #     Generate a final, well-formatted travel response for the user
# # #     combining everything below. Be concise and use headings.
# # #
# # #     Flights:
# # #     {state['flight_results']}
# # #
# # #     Hotels:
# # #     {state['hotel_results']}
# # #
# # #     Itinerary:
# # #     {state['itinerary']}
# # #     """
# # #
# # #     response = llm.invoke([HumanMessage(content=final_prompt)])
# # #
# # #     return {
# # #         "messages": [response],
# # #         "llm_calls": state.get("llm_calls", 0) + 1,
# # #     }
# # #
# # #
# # # # ---------------- Build Graph ----------------
# # # graph = StateGraph(TravelState)
# # #
# # # graph.add_node("flight_agent", flight_agent)
# # # graph.add_node("hotel_agent", hotel_agent)
# # # graph.add_node("itinerary_agent", itinerary_agent)
# # # graph.add_node("final_agent", final_agent)
# # #
# # # graph.add_edge(START, "flight_agent")
# # # graph.add_edge("flight_agent", "hotel_agent")
# # # graph.add_edge("hotel_agent", "itinerary_agent")
# # # graph.add_edge("itinerary_agent", "final_agent")
# # # graph.add_edge("final_agent", END)
# # #
# # #
# # # # ---------------- Checkpointer: Postgres if available, else in-memory ----------------
# # # def _build_checkpointer():
# # #     """
# # #     Tries Postgres first (real long-term memory across restarts).
# # #     Falls back to MemorySaver (in-process only, resets on restart) if
# # #     DATABASE_URL is missing or Postgres isn't reachable -- so the app
# # #     still runs fine while you're setting Postgres up.
# # #     """
# # #     if not DATABASE_URL:
# # #         print("[memory] DATABASE_URL not set -> using in-memory checkpointer "
# # #               "(conversation history will NOT persist across restarts).")
# # #         return MemorySaver()
# # #
# # #     try:
# # #         import psycopg
# # #         from psycopg.rows import dict_row
# # #         from langgraph.checkpoint.postgres import PostgresSaver
# # #
# # #         conn = psycopg.connect(DATABASE_URL, autocommit=True,
# # #                                row_factory=dict_row, connect_timeout=5)
# # #         pg_checkpointer = PostgresSaver(conn)
# # #         pg_checkpointer.setup()
# # #         print("[memory] Connected to Postgres -> using persistent long-term memory.")
# # #         return pg_checkpointer
# # #     except Exception as e:
# # #         print(f"[memory] Postgres unavailable ({e}) -> falling back to "
# # #               f"in-memory checkpointer. Install/start Postgres for persistence.")
# # #         return MemorySaver()
# # #
# # #
# # # checkpointer = _build_checkpointer()
# # # app = graph.compile(checkpointer=checkpointer)
# # #
# # # if __name__ == "__main__":
# # #     config = {"configurable": {"thread_id": "user_aarohi"}}
# # #
# # #     user_input = input("Enter travel request: ")
# # #
# # #     result = app.invoke(
# # #         {
# # #             "messages": [HumanMessage(content=user_input)],
# # #             "user_query": user_input,
# # #             "flight_results": "",
# # #             "hotel_results": "",
# # #             "itinerary": "",
# # #             "llm_calls": 0,
# # #         },
# # #         config=config,
# # #     )
# # #
# # #     print("\nFINAL RESPONSE:\n")
# # #     for msg in result["messages"]:
# # #         print(msg.content)
# # import os
# # import json
# # from datetime import datetime, timedelta
# # from typing import TypedDict, Annotated
# # import operator
# #
# # from langgraph.graph import StateGraph, START, END
# # from langgraph.checkpoint.memory import MemorySaver
# # from langchain_core.messages import (
# #     AnyMessage,
# #     HumanMessage,
# #     AIMessage,
# #     SystemMessage,
# # )
# #
# # from langchain_groq import ChatGroq
# #
# # from tavily_tool import tavily_search
# # from flight_tool import search_flights
# # from dotenv import load_dotenv
# #
# # load_dotenv()
# #
# # DATABASE_URL = os.getenv("DATABASE_URL")
# #
# # # LLM
# # llm = ChatGroq(model="llama-3.3-70b-versatile")
# #
# #
# # # ---------------- State ----------------
# # class TravelState(TypedDict):
# #     messages: Annotated[list[AnyMessage], operator.add]
# #     user_query: str
# #     flight_results: str
# #     dep_iata: str
# #     arr_iata: str
# #     travel_date: str
# #     hotel_results: str
# #     itinerary: str
# #     llm_calls: int
# #
# #
# # # ---------------- Flight Agent ----------------
# # def flight_agent(state: TravelState):
# #     query = state["user_query"]
# #     tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
# #
# #     extraction_prompt = f"""
# #     Extract the departure airport IATA code, arrival airport IATA code,
# #     and travel date from this query.
# #     Query: "{query}"
# #
# #     Respond ONLY in valid JSON, no extra text, no markdown, in this exact format:
# #     {{"dep_iata": "XXX", "arr_iata": "YYY", "date": "YYYY-MM-DD"}}
# #
# #     Use standard 3-letter IATA airport codes (e.g. Delhi -> DEL, Mumbai -> BOM,
# #     Bangalore -> BLR). If no date is mentioned in the query, use "{tomorrow}".
# #     If the query does not mention a departure city at all, default dep_iata to "DEL"
# #     (New Delhi). Never leave dep_iata or arr_iata blank.
# #     """
# #
# #     extraction_response = llm.invoke([
# #         SystemMessage(content="You are a travel query extraction assistant. "
# #                               "Always respond with valid JSON only."),
# #         HumanMessage(content=extraction_prompt),
# #     ])
# #
# #     try:
# #         raw = extraction_response.content.strip()
# #         raw = raw.replace("```json", "").replace("```", "").strip()
# #         print(f"[DEBUG] LLM raw response: {raw}")
# #         codes = json.loads(raw)
# #         dep_iata = (codes.get("dep_iata") or "DEL").upper()
# #         arr_iata = (codes.get("arr_iata") or "").upper()
# #         travel_date = codes.get("date", tomorrow)
# #
# #         if not arr_iata:
# #             raise ValueError("arr_iata missing from LLM response")
# #     except Exception as e:
# #         print(f"[flight_agent] extraction failed: {e}")
# #         return {
# #             "flight_results": "Could not determine flight details from your query.",
# #             "dep_iata": "",
# #             "arr_iata": "",
# #             "travel_date": "",
# #             "messages": [AIMessage(content="Flight search failed - couldn't extract details")],
# #             "llm_calls": state.get("llm_calls", 0) + 1,
# #         }
# #
# #     flight_data = search_flights(dep_iata, arr_iata, travel_date)
# #
# #     return {
# #         "flight_results": flight_data,
# #         "dep_iata": dep_iata,
# #         "arr_iata": arr_iata,
# #         "travel_date": travel_date,
# #         "messages": [AIMessage(content="Flight results fetched")],
# #         "llm_calls": state.get("llm_calls", 0) + 1,
# #     }
# #
# #
# # # ---------------- Hotel Agent ----------------
# # def hotel_agent(state: TravelState):
# #     query = f"Best hotels for {state['user_query']}"
# #     hotel_results = tavily_search(query)
# #     return {
# #         "hotel_results": hotel_results,
# #         "messages": [AIMessage(content="Hotel information fetched")],
# #         "llm_calls": state.get("llm_calls", 0) + 1,
# #     }
# #
# #
# # # ---------------- Itinerary Agent ----------------
# # def itinerary_agent(state: TravelState):
# #     prompt = f"""
# #     Create a travel itinerary.
# #     User Query:
# #     {state['user_query']}
# #
# #     Flight Results:
# #     {state['flight_results']}
# #
# #     Hotel Results:
# #     {state['hotel_results']}
# #     """
# #
# #     response = llm.invoke([
# #         SystemMessage(content="You are an expert travel planner. Create a clear, "
# #                               "day-wise itinerary with approximate costs where possible."),
# #         HumanMessage(content=prompt),
# #     ])
# #
# #     return {
# #         "itinerary": response.content,
# #         "messages": [response],
# #         "llm_calls": state.get("llm_calls", 0) + 1,
# #     }
# #
# #
# # # ---------------- Final Response Agent ----------------
# # def final_agent(state: TravelState):
# #     final_prompt = f"""
# #     Generate a final, well-formatted travel response for the user
# #     combining everything below. Be concise and use headings.
# #
# #     Flights:
# #     {state['flight_results']}
# #
# #     Hotels:
# #     {state['hotel_results']}
# #
# #     Itinerary:
# #     {state['itinerary']}
# #     """
# #
# #     response = llm.invoke([HumanMessage(content=final_prompt)])
# #
# #     return {
# #         "messages": [response],
# #         "llm_calls": state.get("llm_calls", 0) + 1,
# #     }
# #
# #
# # # ---------------- Build Graph ----------------
# # graph = StateGraph(TravelState)
# #
# # graph.add_node("flight_agent", flight_agent)
# # graph.add_node("hotel_agent", hotel_agent)
# # graph.add_node("itinerary_agent", itinerary_agent)
# # graph.add_node("final_agent", final_agent)
# #
# # graph.add_edge(START, "flight_agent")
# # graph.add_edge("flight_agent", "hotel_agent")
# # graph.add_edge("hotel_agent", "itinerary_agent")
# # graph.add_edge("itinerary_agent", "final_agent")
# # graph.add_edge("final_agent", END)
# #
# #
# # # ---------------- Checkpointer: Postgres if available, else in-memory ----------------
# # def _build_checkpointer():
# #     if not DATABASE_URL:
# #         print("[memory] DATABASE_URL not set -> using in-memory checkpointer "
# #               "(conversation history will NOT persist across restarts).")
# #         return MemorySaver()
# #
# #     try:
# #         import psycopg
# #         from psycopg.rows import dict_row
# #         from langgraph.checkpoint.postgres import PostgresSaver
# #
# #         conn = psycopg.connect(DATABASE_URL, autocommit=True,
# #                                row_factory=dict_row, connect_timeout=5)
# #         pg_checkpointer = PostgresSaver(conn)
# #         pg_checkpointer.setup()
# #         print("[memory] Connected to Postgres -> using persistent long-term memory.")
# #         return pg_checkpointer
# #     except Exception as e:
# #         print(f"[memory] Postgres unavailable ({e}) -> falling back to "
# #               f"in-memory checkpointer. Install/start Postgres for persistence.")
# #         return MemorySaver()
# #
# #
# # checkpointer = _build_checkpointer()
# # app = graph.compile(checkpointer=checkpointer)
# #
# # if __name__ == "__main__":
# #     config = {"configurable": {"thread_id": "user_aarohi"}}
# #
# #     user_input = input("Enter travel request: ")
# #
# #     result = app.invoke(
# #         {
# #             "messages": [HumanMessage(content=user_input)],
# #             "user_query": user_input,
# #             "flight_results": "",
# #             "dep_iata": "",
# #             "arr_iata": "",
# #             "travel_date": "",
# #             "hotel_results": "",
# #             "itinerary": "",
# #             "llm_calls": 0,
# #         },
# #         config=config,
# #     )
# #
# #     print("\nFINAL RESPONSE:\n")
# #     for msg in result["messages"]:
# #         print(msg.content)
# import os
# import json
# from datetime import datetime, timedelta
# from typing import TypedDict, Annotated
# import operator
#
# from langgraph.graph import StateGraph, START, END
# from langgraph.checkpoint.memory import MemorySaver
# from langchain_core.messages import (
#     AnyMessage,
#     HumanMessage,
#     AIMessage,
#     SystemMessage,
# )
#
# from langchain_groq import ChatGroq
#
# from tavily_tool import tavily_search
# from flight_tool import search_flights
# from dotenv import load_dotenv
#
# load_dotenv()
#
# DATABASE_URL = os.getenv("DATABASE_URL")
#
# # LLM
# llm = ChatGroq(model="llama-3.3-70b-versatile")
#
#
# # ---------------- State ----------------
# class TravelState(TypedDict):
#     messages: Annotated[list[AnyMessage], operator.add]
#     user_query: str
#     flight_results: str
#     dep_iata: str
#     arr_iata: str
#     travel_date: str
#     hotel_results: str
#     itinerary: str
#     llm_calls: int
#
#
# # ---------------- Flight Agent ----------------
# def flight_agent(state: TravelState):
#     query = state["user_query"]
#     tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
#
#     extraction_prompt = f"""
#     Extract the departure airport IATA code, arrival airport IATA code,
#     and travel date from this query.
#     Query: "{query}"
#
#     Respond ONLY in valid JSON, no extra text, no markdown, in this exact format:
#     {{"dep_iata": "XXX", "arr_iata": "YYY", "date": "YYYY-MM-DD"}}
#
#     Use standard 3-letter IATA airport codes (e.g. Delhi -> DEL, Mumbai -> BOM,
#     Bangalore -> BLR). If no date is mentioned in the query, use "{tomorrow}".
#     If the query does not mention a departure city at all, default dep_iata to "DEL"
#     (New Delhi).
#     If the destination is a country or region name rather than a specific city
#     (e.g. "Japan", "Thailand", "Italy"), use that country's main international
#     gateway airport (e.g. Japan -> "NRT" (Tokyo Narita), Thailand -> "BKK",
#     Italy -> "FCO", France -> "CDG", UAE -> "DXB", Indonesia -> "DPS" for Bali).
#     Never leave dep_iata or arr_iata blank — always make your best guess.
#     """
#
#     extraction_response = llm.invoke([
#         SystemMessage(content="You are a travel query extraction assistant. "
#                               "Always respond with valid JSON only."),
#         HumanMessage(content=extraction_prompt),
#     ])
#
#     try:
#         raw = extraction_response.content.strip()
#         raw = raw.replace("```json", "").replace("```", "").strip()
#         print(f"[DEBUG] LLM raw response: {raw}")
#         codes = json.loads(raw)
#         dep_iata = (codes.get("dep_iata") or "DEL").upper()
#         arr_iata = (codes.get("arr_iata") or "").upper()
#         travel_date = codes.get("date", tomorrow)
#
#         if not arr_iata:
#             raise ValueError("arr_iata missing from LLM response")
#     except Exception as e:
#         print(f"[flight_agent] extraction failed: {e}")
#         return {
#             "flight_results": "Could not determine flight details from your query.",
#             "dep_iata": "",
#             "arr_iata": "",
#             "travel_date": "",
#             "messages": [AIMessage(content="Flight search failed - couldn't extract details")],
#             "llm_calls": state.get("llm_calls", 0) + 1,
#         }
#
#     flight_data = search_flights(dep_iata, arr_iata, travel_date)
#
#     return {
#         "flight_results": flight_data,
#         "dep_iata": dep_iata,
#         "arr_iata": arr_iata,
#         "travel_date": travel_date,
#         "messages": [AIMessage(content="Flight results fetched")],
#         "llm_calls": state.get("llm_calls", 0) + 1,
#     }
#
#
# # ---------------- Hotel Agent ----------------
# def hotel_agent(state: TravelState):
#     query = f"Best hotels for {state['user_query']}"
#     hotel_results = tavily_search(query)
#     return {
#         "hotel_results": hotel_results,
#         "messages": [AIMessage(content="Hotel information fetched")],
#         "llm_calls": state.get("llm_calls", 0) + 1,
#     }
#
#
# # ---------------- Itinerary Agent ----------------
# def itinerary_agent(state: TravelState):
#     prompt = f"""
#     Create a travel itinerary.
#     User Query:
#     {state['user_query']}
#
#     Flight Results:
#     {state['flight_results']}
#
#     Hotel Results:
#     {state['hotel_results']}
#     """
#
#     response = llm.invoke([
#         SystemMessage(content="You are an expert travel planner. Create a clear, "
#                               "day-wise itinerary with approximate costs where possible."),
#         HumanMessage(content=prompt),
#     ])
#
#     return {
#         "itinerary": response.content,
#         "messages": [response],
#         "llm_calls": state.get("llm_calls", 0) + 1,
#     }
#
#
# # ---------------- Final Response Agent ----------------
# def final_agent(state: TravelState):
#     final_prompt = f"""
#     Generate a final, well-formatted travel response for the user
#     combining everything below. Be concise and use headings.
#
#     Flights:
#     {state['flight_results']}
#
#     Hotels:
#     {state['hotel_results']}
#
#     Itinerary:
#     {state['itinerary']}
#     """
#
#     response = llm.invoke([HumanMessage(content=final_prompt)])
#
#     return {
#         "messages": [response],
#         "llm_calls": state.get("llm_calls", 0) + 1,
#     }
#
#
# # ---------------- Build Graph ----------------
# graph = StateGraph(TravelState)
#
# graph.add_node("flight_agent", flight_agent)
# graph.add_node("hotel_agent", hotel_agent)
# graph.add_node("itinerary_agent", itinerary_agent)
# graph.add_node("final_agent", final_agent)
#
# graph.add_edge(START, "flight_agent")
# graph.add_edge("flight_agent", "hotel_agent")
# graph.add_edge("hotel_agent", "itinerary_agent")
# graph.add_edge("itinerary_agent", "final_agent")
# graph.add_edge("final_agent", END)
#
#
# # ---------------- Checkpointer: Postgres if available, else in-memory ----------------
# def _build_checkpointer():
#     if not DATABASE_URL:
#         print("[memory] DATABASE_URL not set -> using in-memory checkpointer "
#               "(conversation history will NOT persist across restarts).")
#         return MemorySaver()
#
#     try:
#         import psycopg
#         from psycopg.rows import dict_row
#         from langgraph.checkpoint.postgres import PostgresSaver
#
#         conn = psycopg.connect(DATABASE_URL, autocommit=True,
#                                row_factory=dict_row, connect_timeout=5)
#         pg_checkpointer = PostgresSaver(conn)
#         pg_checkpointer.setup()
#         print("[memory] Connected to Postgres -> using persistent long-term memory.")
#         return pg_checkpointer
#     except Exception as e:
#         print(f"[memory] Postgres unavailable ({e}) -> falling back to "
#               f"in-memory checkpointer. Install/start Postgres for persistence.")
#         return MemorySaver()
#
#
# checkpointer = _build_checkpointer()
# app = graph.compile(checkpointer=checkpointer)
#
# if __name__ == "__main__":
#     config = {"configurable": {"thread_id": "user_aarohi"}}
#
#     user_input = input("Enter travel request: ")
#
#     result = app.invoke(
#         {
#             "messages": [HumanMessage(content=user_input)],
#             "user_query": user_input,
#             "flight_results": "",
#             "dep_iata": "",
#             "arr_iata": "",
#             "travel_date": "",
#             "hotel_results": "",
#             "itinerary": "",
#             "llm_calls": 0,
#         },
#         config=config,
#     )
#
#     print("\nFINAL RESPONSE:\n")
#     for msg in result["messages"]:
#         print(msg.content)
import os
import json
from datetime import datetime, timedelta
from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from langchain_groq import ChatGroq

from tavily_tool import tavily_search
from flight_tool import search_flights
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# LLM
llm = ChatGroq(model="llama-3.3-70b-versatile")


# ---------------- State ----------------
class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    dep_iata: str
    arr_iata: str
    travel_date: str
    destination_city: str
    hotel_results: str
    itinerary: str
    llm_calls: int


# ---------------- Flight Agent ----------------
def flight_agent(state: TravelState):
    query = state["user_query"]
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    extraction_prompt = f"""
    Extract the departure airport IATA code, arrival airport IATA code,
    and travel date from this query.
    Query: "{query}"

    Respond ONLY in valid JSON, no extra text, no markdown, in this exact format:
    {{"dep_iata": "XXX", "arr_iata": "YYY", "date": "YYYY-MM-DD", "destination_city": "CityName"}}

    "destination_city" should be the common human-readable name of the arrival
    city (e.g. "Tokyo", "Paris", "Mumbai") â€” not the airport code.

    Use standard 3-letter IATA airport codes (e.g. Delhi -> DEL, Mumbai -> BOM,
    Bangalore -> BLR). If no date is mentioned in the query, use "{tomorrow}".
    If the query does not mention a departure city at all, default dep_iata to "DEL"
    (New Delhi).
    If the destination is a country or region name rather than a specific city
    (e.g. "Japan", "Thailand", "Italy"), use that country's main international
    gateway airport (e.g. Japan -> "NRT" (Tokyo Narita), Thailand -> "BKK",
    Italy -> "FCO", France -> "CDG", UAE -> "DXB", Indonesia -> "DPS" for Bali).
    Never leave dep_iata or arr_iata blank â€” always make your best guess.
    """

    extraction_response = llm.invoke([
        SystemMessage(content="You are a travel query extraction assistant. "
                              "Always respond with valid JSON only."),
        HumanMessage(content=extraction_prompt),
    ])

    try:
        raw = extraction_response.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        print(f"[DEBUG] LLM raw response: {raw}")
        codes = json.loads(raw)
        dep_iata = (codes.get("dep_iata") or "DEL").upper()
        arr_iata = (codes.get("arr_iata") or "").upper()
        travel_date = codes.get("date", tomorrow)
        destination_city = codes.get("destination_city") or arr_iata

        if not arr_iata:
            raise ValueError("arr_iata missing from LLM response")
    except Exception as e:
        print(f"[flight_agent] extraction failed: {e}")
        return {
            "flight_results": "Could not determine flight details from your query.",
            "dep_iata": "",
            "arr_iata": "",
            "travel_date": "",
            "destination_city": "",
            "messages": [AIMessage(content="Flight search failed - couldn't extract details")],
            "llm_calls": state.get("llm_calls", 0) + 1,
        }

    flight_data = search_flights(dep_iata, arr_iata, travel_date)

    return {
        "flight_results": flight_data,
        "dep_iata": dep_iata,
        "arr_iata": arr_iata,
        "travel_date": travel_date,
        "destination_city": destination_city,
        "messages": [AIMessage(content="Flight results fetched")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ---------------- Hotel Agent ----------------
def hotel_agent(state: TravelState):
    query = f"Best hotels for {state['user_query']}"
    hotel_results = tavily_search(query)
    return {
        "hotel_results": hotel_results,
        "messages": [AIMessage(content="Hotel information fetched")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ---------------- Itinerary Agent ----------------
def itinerary_agent(state: TravelState):
    prompt = f"""
    Create a travel itinerary.
    User Query:
    {state['user_query']}

    Flight Results:
    {state['flight_results']}

    Hotel Results:
    {state['hotel_results']}
    """

    response = llm.invoke([
        SystemMessage(content="You are an expert travel planner. Create a clear, "
                              "day-wise itinerary with approximate costs where possible."),
        HumanMessage(content=prompt),
    ])

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ---------------- Final Response Agent ----------------
def final_agent(state: TravelState):
    final_prompt = f"""
    Generate a final, well-formatted travel response for the user
    combining everything below. Be concise and use headings.

    Flights:
    {state['flight_results']}

    Hotels:
    {state['hotel_results']}

    Itinerary:
    {state['itinerary']}
    """

    response = llm.invoke([HumanMessage(content=final_prompt)])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ---------------- Build Graph ----------------
graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)


# ---------------- Checkpointer: Postgres if available, else in-memory ----------------
def _build_checkpointer():
    if not DATABASE_URL:
        print("[memory] DATABASE_URL not set -> using in-memory checkpointer "
              "(conversation history will NOT persist across restarts).")
        return MemorySaver()

    try:
        import psycopg
        from psycopg.rows import dict_row
        from langgraph.checkpoint.postgres import PostgresSaver

        conn = psycopg.connect(DATABASE_URL, autocommit=True,
                               row_factory=dict_row, connect_timeout=5)
        pg_checkpointer = PostgresSaver(conn)
        pg_checkpointer.setup()
        print("[memory] Connected to Postgres -> using persistent long-term memory.")
        return pg_checkpointer
    except Exception as e:
        print(f"[memory] Postgres unavailable ({e}) -> falling back to "
              f"in-memory checkpointer. Install/start Postgres for persistence.")
        return MemorySaver()


checkpointer = _build_checkpointer()
app = graph.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "user_aarohi"}}

    user_input = input("Enter travel request: ")

    result = app.invoke(
        {
            "messages": [HumanMessage(content=user_input)],
            "user_query": user_input,
            "flight_results": "",
            "dep_iata": "",
            "arr_iata": "",
            "travel_date": "",
            "destination_city": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0,
        },
        config=config,
    )

    print("\nFINAL RESPONSE:\n")
    for msg in result["messages"]:
        print(msg.content)
