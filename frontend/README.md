# Malicious Content Detection UI

React + TypeScript dashboard for interacting with the detection API. Built with Vite and Material-UI.

## Features

- Single text analysis with confidence scores and risk levels
- Batch CSV upload for bulk processing
- Configurable API endpoint and key (persisted in local storage)
- Responsive layout for desktop and mobile

## Setup

Requires Node.js 18+ and the backend API running.

```bash
npm install
npm run dev
```

Connects to `http://localhost:8000` by default. Change via the Connection panel in the UI or in `.env`:

```
VITE_API_URL=http://localhost:8000
```

## Build

```bash
npm run build    # Production build
npm run preview  # Preview the build locally
npm run lint     # ESLint
```

## Docker

Included in the root `docker-compose.yml`. To build standalone:

```bash
docker build -t detection-ui --build-arg VITE_API_URL=http://localhost:8000 .
```
