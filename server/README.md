# Overview
This project is managed using `pyproject.toml` and the [`uv`](https://github.com/astral-sh/uv) package manager for fast Python dependency management.

## 1. Test with Web Client

### Set Up Environment Variables
Based on .env-sample.txt, create and construct your .env file to allow your local app to access your Azure resource.

### Run the App Locally
1. Run the local server:

    ```shell
    uv run server.py
    ```

3. Once the app is running, open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser (or click the printed URL in the terminal).

4. On the page, click **Start** to begin speaking with the agent using your browser’s microphone and speaker.

### Run with Docker (Alternative)

If you prefer Docker or are running in GitHub Codespaces:

1. Build the image:

    ```
    docker build -t voiceagent .
    ```

2. Run the image with local environment variables:

    ```
    docker run --env-file .env -p 8000:8000 -it voiceagent
    ```
3. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and click **Start** to interact with the agent.

## 2. Test with ACS Client (Phone Call)

To test Azure Communication Services (ACS) locally, we’ll expose the local server using **Azure DevTunnels**.

> DevTunnels allow public HTTP/S access to your local environment — ideal for webhook testing.

1. [Install Azure Dev CLI](https://learn.microsoft.com/azure/developer/dev-tunnels/overview) if not already installed.

2. Log in and create a tunnel:

    ```bash
    devtunnel login
    devtunnel create --allow-anonymous
    devtunnel port create -p 8000
    devtunnel host
    ```

3. The final command will output a URL like:

    ```
    https://<your-tunnel>.devtunnels.ms:8000
    ```

4. Add this URL to your `.env` file under:

    ```
    ACS_DEV_TUNNEL=https://<your-tunnel>.devtunnels.ms:8000
    ```

### Set Up Incoming Call Event

1. Go to your **Communication Services** resource in the Azure Portal.
2. In the left menu, click **Events** → **+ Event Subscription**.
3. Use the following settings:
   - **Event type**: `IncomingCall`
   - **Endpoint type**: `Web Hook`
   - **Endpoint URL**:  
     ```
     https://<your-tunnel>.devtunnels.ms:8000/acs/incomingcall
     ```

> Ensure both your local Python server and DevTunnel are running before creating the subscription.

### Call the Agent

1. [Get a phone number](https://learn.microsoft.com/azure/communication-services/quickstarts/telephony/get-phone-number?tabs=windows&pivots=platform-azp-new) for your ACS resource if not already provisioned.
2. Call the number. Your call will route to your local agent.

## Recap

- Use the **web client** for fast local testing.
- Use **DevTunnel + ACS** to simulate phone calls and test telephony integration.
- Customize the `.env` file, system prompts, and runtime behavior to fit your use case.

## Booking Integration (Google Calendar + SMS)

The backend exposes booking APIs used by the `/booking` frontend:

- `GET /api/bookings/availability?customerId=<id>&start=<iso>&end=<iso>`
- `POST /api/bookings`
- `GET /api/admin/reports/summary?days=30`
- `GET /api/admin/bookings?limit=300`
- `GET /api/admin/calls?limit=300`

To enable Google Calendar sync and SMS reminders, add these environment variables:

```env
GOOGLE_SERVICE_ACCOUNT_JSON=<service account JSON string>
# or
GOOGLE_SERVICE_ACCOUNT_FILE=<absolute path to service account JSON>
GOOGLE_CALENDAR_ID=<calendar id>
BOOKING_TIMEZONE=America/Chicago

ACS_SMS_FROM=<ACS SMS-enabled E.164 phone number>
ACS_SMS_CONNECTION_STRING=<Optional dedicated ACS SMS connection string; defaults to ACS_CONNECTION_STRING>
ACS_SMS_TAG=booking-reminder
BOOKING_REMINDER_LEAD_HOURS=48
BOOKING_DB_PATH=/tmp/bookings.db
BOOKING_DEFAULT_PARTY_REVENUE=350
BOOKING_DEFAULT_CAMP_REVENUE=125
```

For Azure deployments, store SMS connection string as an environment secret before provisioning:

```bash
azd env set ACS_SMS_CONNECTION_STRING "<your-acs-sms-connection-string>"
azd env set ACS_SMS_FROM "+18337939008"
azd env set BOOKING_REMINDER_LEAD_HOURS "48"
azd provision
azd deploy
```

Notes:
- The Google service account must have write access to the configured calendar.
- Phone numbers are normalized to E.164 for SMS.
- One SMS reminder is sent per booking, scheduled 48 hours (2 days) before the event by default.
- Reminders are persisted in SQLite at `BOOKING_DB_PATH`.
- Voice/call session data is persisted to `call_logs` in the same SQLite database.
