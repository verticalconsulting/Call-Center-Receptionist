# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a **Call Center Voice Agent Accelerator** built with Azure Voice Live API and Azure Communication Services (ACS). It provides real-time speech-to-speech voice agents for call center scenarios with two client modes: web browser (for testing) and ACS phone calls (for production).

## Technology Stack

- **Backend**: Python 3.9+ with Quart (async Flask-like framework)
- **Package Manager**: UV (fast Python dependency management via `pyproject.toml`)
- **Infrastructure**: Azure Bicep templates for IaC
- **Deployment**: Azure Developer CLI (`azd`)
- **Key Azure Services**:
  - Azure Voice Live API (Speech-to-speech with integrated ASR, LLM, TTS)
  - Azure Communication Services (telephony/call automation)
  - Azure Container Apps (hosting)
  - Azure Container Registry
  - Azure Key Vault (stores ACS call + SMS connection strings)

## Development Commands

### Local Development

#### Backend (server/ directory)

```bash
# Run the Python server
uv run server.py

# Access simple voice demo at http://127.0.0.1:8000
# Access booking UI at http://127.0.0.1:8000/booking
```

#### Frontend (frontend/ directory)

```bash
# Install dependencies
npm install

# Start dev server (with HMR)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The frontend dev server runs on port 3000 and proxies WebSocket requests to the Python backend on port 8000.

### Docker Development

```bash
# Build image
docker build -t voiceagent -f server/Dockerfile .

# Run with environment variables
docker run --env-file .env -p 8000:8000 -it voiceagent
```

### Deployment

```bash
# Login to Azure
azd auth login

# Deploy all resources (initial + updates)
azd up

# Deploy code changes only
azd deploy

# Clean up all resources
azd down
```

`azd` deploys the `app` service using repository root as build context (`azure.yaml` -> `services.app.project: .`) so the image includes both `server/` and `frontend/`.

### Testing with ACS Phone Client (Local)

Use Azure DevTunnels to expose local server for webhook testing:

```bash
devtunnel login
devtunnel create --allow-anonymous
devtunnel port create -p 8000
devtunnel host
```

## Architecture

### Core Application Structure

```
server/
├── server.py                    # Main Quart application with routes
├── customer_routing.json        # Multi-customer phone number routing config
├── app/
│   └── handler/
│       ├── acs_event_handler.py # Processes ACS incoming calls and callbacks
│       └── acs_media_handler.py # Manages audio streaming to Voice Live API
├── prompts/                     # Customer-specific system prompts
│   ├── grace_intake_agent.txt
│   ├── customer_xyz_agent.txt
│   ├── dbat_pearl_agent.txt
│   └── README.md
├── static/                      # Static files
│   ├── index.html               # Simple voice demo (legacy)
│   ├── audio-processor.js
│   └── booking/                 # React booking UI (built from frontend/)
└── conversation_logs/           # Saved conversation transcripts

frontend/                        # React booking interface
├── src/
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components
│   │   └── booking/             # Booking form components
│   ├── pages/
│   │   ├── CustomerSelection.jsx  # Landing page
│   │   ├── BookingPage.jsx        # Booking forms
│   │   └── VoiceDemo.jsx          # Voice agent demo
│   ├── hooks/
│   │   └── useVoiceAgent.js     # WebSocket voice integration
│   └── App.jsx
├── package.json
├── vite.config.js
└── README.md
```

### Request Flow

1. **React Booking UI**: Browser → `/booking` → React app (customer selection, forms, voice demo)
2. **Web Client Voice Mode**: Browser → `/web/ws?customerId=<customer>` WebSocket → `ACSMediaHandler` → Voice Live API
3. **ACS Phone Mode**:
   - Phone Call → ACS IncomingCall event → `/acs/incomingcall`
   - Extract called phone number → Look up customer in `customer_routing.json`
   - Answer call with media streaming → `/acs/ws?customerId=<customer>` WebSocket
   - `ACSMediaHandler` loads customer-specific prompt and voice settings → Voice Live API

### Key Handlers

- **AcsEventHandler** (`acs_event_handler.py`): Handles EventGrid subscription validation and incoming call events. Extracts the called phone number, looks up customer configuration from `customer_routing.json`, and answers calls with `MediaStreamingOptions` configured for bidirectional audio. Passes `customerId` via WebSocket query parameters.
- **ACSMediaHandler** (`acs_media_handler.py`): Establishes WebSocket connection to Voice Live API with customer-specific configuration. Loads appropriate system prompt and voice settings based on `customer_id`. Manages audio queues and handles bidirectional audio streaming. Uses managed identity or API key authentication.

### Infrastructure (infra/)

Bicep modules provision:
- User-assigned managed identity (for Key Vault and AI services access)
- AI Services (Voice Live API endpoint)
- Communication Services (telephony)
- Container Apps + Container Registry
- Key Vault (stores ACS call and SMS connection strings as secrets)
- Monitoring (Log Analytics, Application Insights)

The main deployment is subscription-scoped (`infra/main.bicep`). Note: Limited to `eastus2` and `swedencentral` regions due to Voice Live API availability.

## Environment Configuration

Create `.env` file in `server/` directory based on `.env-sample.txt`:

```
AZURE_VOICE_LIVE_API_KEY=<AI Foundry resource key>
AZURE_VOICE_LIVE_ENDPOINT=<AI Foundry resource endpoint>
VOICE_LIVE_MODEL=gpt-realtime
ACS_CONNECTION_STRING=<Communication Services connection string>
ACS_SMS_CONNECTION_STRING=<Optional dedicated ACS SMS connection string; falls back to ACS_CONNECTION_STRING>
ACS_SMS_FROM=<ACS SMS enabled phone number in E.164 format>
ACS_DEV_TUNNEL=<Optional: DevTunnel URL for local ACS testing>
```

When deployed to Azure, the container app uses:
- Managed Identity for Voice Live API authentication
- Key Vault secret references for ACS connection strings (`ACS_CONNECTION_STRING`, `ACS_SMS_CONNECTION_STRING`)

## Voice Live API Configuration

Session configuration is defined in `acs_media_handler.py:session_config()`:
- **Turn Detection**: Azure Semantic VAD with end-of-utterance detection
- **Audio Processing**: Deep noise suppression and server echo cancellation
- **Voice**: Configurable per-customer Azure Neural TTS voice (default: en-US-Emma2:DragonHDLatestNeural)
- **Instructions**: Loaded dynamically from customer-specific prompt files in [server/prompts/](server/prompts/)

### Multi-Customer Configuration

The system supports multiple customers with different phone numbers, each with their own:
- System prompt and agent persona
- Voice settings (voice name, temperature)
- Custom configuration per phone number

#### Customer Routing Setup

1. **Configure phone number mapping** in [server/customer_routing.json](server/customer_routing.json):
   ```json
   {
     "customers": {
       "+18005551234": {
         "customer_id": "mercy_house",
         "customer_name": "Mercy House & Sacred Grove",
         "prompt_file": "grace_intake_agent.txt",
         "voice_name": "en-US-Emma2:DragonHDLatestNeural",
         "voice_temperature": 0.8
       },
       "+18005555678": {
         "customer_id": "customer_xyz",
         "customer_name": "Customer XYZ Healthcare",
         "prompt_file": "customer_xyz_agent.txt"
       }
     },
     "default": {
       "customer_id": "default",
       "prompt_file": "grace_intake_agent.txt"
     }
   }
   ```

2. **Create system prompts** in [server/prompts/](server/prompts/):
   - Each customer can have a unique prompt file
   - See [server/prompts/README.md](server/prompts/README.md) for prompt creation guidelines
   - Example prompts: `grace_intake_agent.txt`, `customer_xyz_agent.txt`

3. **Restart server** to load new configuration

#### Adding a New Customer

To add a new customer with a different phone number:

1. Create new prompt file: `server/prompts/new_customer_agent.txt`
2. Add phone mapping to `server/customer_routing.json`
3. Provision phone number in Azure Communication Services
4. Test by calling the phone number

**Note**: All customers share the same Azure infrastructure (Container App, Voice Live API endpoint). No separate deployments needed.

## Post-Deployment Setup

After `azd up`:
1. Navigate to the Container App URL to test the web client
2. For phone testing:
   - Create Event Grid subscription for IncomingCall events pointing to `https://<container-app-url>/acs/incomingcall`
   - Provision a phone number for each customer in ACS
   - Configure phone numbers in `customer_routing.json`
   - Call the number to test customer-specific voice agent

## Conversation Logging and Analysis

The system automatically logs all conversations with detailed timing information for analysis and quality assurance.

### Automatic Logging

Every session is automatically saved to [server/conversation_logs/](server/conversation_logs/) as a JSON file containing:
- Full conversation transcript (user and assistant)
- Precise timestamps for each event
- Time delays/pauses between utterances
- Speech detection events (started/stopped)
- Session metadata (duration, model, endpoint)

### Analyzing Conversations

Use the conversation analyzer tool to review and analyze logged conversations:

```bash
# View most recent conversation with timing analysis
python server/conversation_analyzer.py

# Analyze specific conversation log
python server/conversation_analyzer.py server/conversation_logs/conversation_20251125_103000_abc123.json

# List all available conversation logs
python server/conversation_analyzer.py --list

# Export clean transcript to text file
python server/conversation_analyzer.py --export transcript.txt
```

### Key Metrics

The analyzer provides:
- **Response Times**: How quickly Grace responds after user stops speaking
- **Turn-taking Analysis**: User and assistant turn counts
- **Pause Detection**: Identifies significant pauses (>2s) in conversation
- **Conversation Flow**: Timeline view showing exact timing of all events

### Privacy and Data Retention

Conversation logs may contain sensitive caller information (names, phone numbers, personal situations). Handle according to your organization's privacy policies:
- Logs are saved locally and NOT automatically sent anywhere
- Implement log rotation/cleanup based on your retention requirements
- Log files are gitignored by default (`.gitignore` excludes `*.json` files in conversation_logs/)

See [server/conversation_logs/README.md](server/conversation_logs/README.md) for detailed documentation.

## Important Notes

- **Security**: ACS call and SMS connection strings are stored in Key Vault. Container app retrieves them via secret references.
- **Authentication**: Production deployments use managed identity for Voice Live API. Local development uses API key.
- **Region Constraints**: Voice Live API is only available in specific regions (swedencentral strongly recommended).
- **WebSocket Endpoints**:
  - `/web/ws` for browser clients (raw audio, uses default customer)
  - `/acs/ws?customerId=<customer>` for ACS calls (PCM 24kHz mono, customer-specific routing)
- **Storage**: Conversation logs are stored in Azure Storage Blobs when `AZURE_STORAGE_ACCOUNT_URL` is configured (managed identity access).
