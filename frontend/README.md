# Malicious Content Detection UI

A modern React + TypeScript application for interacting with the Malicious Content Detection API.

## Features
-   **Single Text Analysis**: Real-time analysis with confidence scores and risk levels.
-   **Batch Processing**: Upload CSV files for bulk analysis.
-   **Secure Connection**: Configurable API Endpoint and API Key (persisted locally).
-   **Responsive Design**: Optimized for desktop and mobile.

## Setup

### Prerequisites
-   Node.js 18+
-   Back-end API running

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

### Configuration
By default, the UI connects to `http://localhost:8000`.
You can change this in the "Connection" panel or via `.env`:

```
VITE_API_URL=http://localhost:8000
```

## Docker

The frontend is included in the main `docker-compose.yml`.
To build manually:

```bash
docker build -t detection-ui .
```
