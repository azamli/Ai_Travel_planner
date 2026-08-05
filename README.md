# AI Travel Planner 

This is my AI-based travel planning project. You just type something like "plan a trip from Delhi to Mumbai" and it finds flights, suggests hotels, and creates a day-by-day itinerary for you automatically.

Made by **Azam Ali** 

## What it does

- You type your trip in plain English (or Hinglish 😄)
- It searches real flights and shows prices
- It suggests hotels for your destination
- It creates a full itinerary using AI
- You can click "Book on Skyscanner" or "Book Hotel" to actually book
- It keeps a history of your past searches
- You can download the whole plan as a text file

## How I built it

**Backend:**
- Python + FastAPI
- LangGraph (to run multiple AI agents one after another — flight agent, hotel agent, itinerary agent)
- Groq API for the AI/LLM part
- Duffel API for real flight search
- Tavily API for hotel search

**Frontend:**
- React (made with Vite)
- Plain CSS, no framework

## How to run it on your own computer

**Backend:**
```
pip install -r requirements.txt
```

Make a `.env` file and add:
```
GROQ_API_KEY=your_key_here
DUFFEL_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
```

Then run:
```
uvicorn Ai_flight_agent_FASTAPI:api --reload --port 8001
```

**Frontend:**
```
cd frontend
npm install
npm run dev
```

## Deployed on

- Backend → Render
- Frontend → Vercel

## Contact me

- LinkedIn: https://www.linkedin.com/in/azam-ali-38276a29a/
- Instagram: https://www.instagram.com/azam_ansari57255/
- Email: azamansari57255@gmail.com
