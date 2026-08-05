# AI Travel Planner — Frontend

This is the frontend for my AI Travel Planner project. It's a React app (built with Vite) that lets you type a trip in plain English and get flights, hotels, and a full itinerary back from the backend.

## Tech Used

- React (Vite)
- Plain CSS (no framework like Tailwind/Bootstrap)

## Features

- Search bar to type your trip
- Destination cards (Tokyo, Paris, Bangkok, Rome, Dubai) you can click to auto-search
- Quick prompt suggestions
- Shows flight results with prices + "Book on Skyscanner" button
- Shows hotel results + "Book Hotel" button (Booking.com)
- Shows AI-generated itinerary
- History sidebar to revisit past searches
- Download full plan as a text file

## How to run locally

```
npm install
npm run dev
```

This will start the app at `http://localhost:5173` (or another port if that one's busy).

## Connecting to backend

Open `src/App.jsx` and check this line near the top:

```js
const API_BASE = "http://localhost:8001";
```

Change this to wherever your backend is running. For local testing it stays as above. After deploying the backend (e.g. on Render), change it to the live backend URL, like:

```js
const API_BASE = "https://your-backend.onrender.com";
```

## Deployment

Deployed on **Vercel**.

- Root directory: `frontend`
- Vercel auto-detects Vite and builds it — no extra config needed
- Make sure `API_BASE` points to the live backend before deploying

## Folder structure

```
frontend/
├── public/
│   ├── azam.jpg
│   ├── favicon.svg
│   └── icons.svg
├── src/
│   ├── App.jsx
│   ├── App.css
│   └── main.jsx
├── index.html
├── package.json
└── vite.config.js
```

## Made by

Azam Ali & Aalam Ansari
