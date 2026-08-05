import uuid
from urllib.parse import quote
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from Ai_flight_agent import app as travel_graph

api = FastAPI(title="Travel Agent API")

api.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+|https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TravelRequest(BaseModel):
    query: str
    thread_id: str | None = None


class TravelResponse(BaseModel):
    thread_id: str
    flight_results: str
    hotel_results: str
    itinerary: str
    final_response: str
    dep_iata: str = ""
    arr_iata: str = ""
    travel_date: str = ""
    skyscanner_url: str = ""
    booking_url: str = ""


@api.get("/")
def health_check():
    return {"status": "ok"}


@api.post("/travel-plan", response_model=TravelResponse)
def create_travel_plan(request: TravelRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = travel_graph.invoke(
            {
                "messages": [HumanMessage(content=request.query)],
                "user_query": request.query,
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    final_msg = result["messages"][-1].content if result["messages"] else ""

    dep_iata = result.get("dep_iata", "")
    arr_iata = result.get("arr_iata", "")
    travel_date = result.get("travel_date", "")

    skyscanner_url = ""
    if dep_iata and arr_iata and travel_date:
        try:
            yy_mm_dd = travel_date.replace("-", "")[2:]  # YYYY-MM-DD -> YYMMDD
            skyscanner_url = (
                f"https://www.skyscanner.co.in/transport/flights/"
                f"{dep_iata.lower()}/{arr_iata.lower()}/{yy_mm_dd}/"
            )
        except Exception:
            skyscanner_url = ""

    destination_city = result.get("destination_city", "")
    booking_url = ""
    if destination_city:
        try:
            checkin = travel_date or (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            checkout_dt = datetime.strptime(checkin, "%Y-%m-%d") + timedelta(days=3)
            checkout = checkout_dt.strftime("%Y-%m-%d")
            booking_url = (
                f"https://www.booking.com/searchresults.html?"
                f"ss={quote(destination_city)}&checkin={checkin}&checkout={checkout}"
            )
        except Exception:
            booking_url = ""

    return TravelResponse(
        thread_id=thread_id,
        flight_results=result.get("flight_results", ""),
        hotel_results=result.get("hotel_results", ""),
        itinerary=result.get("itinerary", ""),
        final_response=final_msg,
        dep_iata=dep_iata,
        arr_iata=arr_iata,
        travel_date=travel_date,
        skyscanner_url=skyscanner_url,
        booking_url=booking_url,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("Ai_flight_agent_FASTAPI:api", host="0.0.0.0", port=8000, reload=True)
