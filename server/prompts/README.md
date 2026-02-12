# Voice Agent System Prompts

This directory contains system prompts for different customer configurations. Each prompt file defines the persona, behavior, and knowledge base for the voice agent.

## Available Prompts

### grace_intake_agent.txt
**Customer**: Mercy House & Sacred Grove
**Persona**: Grace - Professional intake receptionist
**Purpose**: Handling intake calls for substance abuse recovery facilities

### customer_xyz_agent.txt
**Customer**: Customer XYZ Healthcare (Example)
**Persona**: Healthcare intake agent
**Purpose**: General healthcare appointment scheduling and inquiries

## Creating New Prompts

To add a new customer prompt:

1. **Create prompt file**: Add a new `.txt` file in this directory (e.g., `new_customer_agent.txt`)

2. **Update routing config**: Add entry to `server/customer_routing.json`:
   ```json
   {
     "customers": {
       "+1234567890": {
         "customer_id": "new_customer",
         "customer_name": "New Customer Inc",
         "prompt_file": "new_customer_agent.txt"
       }
     }
   }
   ```

3. **Test locally**: Restart the server and test via web client or phone

## Prompt Structure Guidelines

A good system prompt should include:

### 1. Identity & Role
```
You are [name], [role description] for [organization].
```

### 2. Primary Responsibilities
List 3-5 key tasks the agent should handle:
```
Your role is to:
1. [First responsibility]
2. [Second responsibility]
...
```

### 3. Communication Style
Define tone, pacing, and interaction patterns:
```
Communication Style:
- [Tone: professional, casual, empathetic, etc.]
- [Pacing: natural pauses, concise responses]
- [Active listening behaviors]
```

### 4. Important Guidelines
Security, compliance, and operational rules:
```
Important Guidelines:
- What information can be collected
- What NOT to do (medical advice, financial info, etc.)
- Escalation procedures
- Compliance requirements
```

### 5. Organization Context
Relevant facts about the organization:
```
Organization Information:
- Services offered
- Operating hours
- Contact information
- Special programs
```

## Voice Configuration

Beyond the prompt text, you can customize the voice in `customer_routing.json`:

```json
{
  "voice_name": "en-US-Emma2:DragonHDLatestNeural",
  "voice_temperature": 0.8
}
```

**Available voices**: See [Azure Neural Voice Gallery](https://speech.microsoft.com/portal/voicegallery)

**Temperature**:
- `0.6-0.7`: More consistent, professional
- `0.8-0.9`: More expressive, conversational
- `1.0`: Maximum expressiveness

## Testing Prompts

### Web Client Testing
1. Start server: `uv run server.py`
2. Navigate to `http://localhost:8000`
3. Test the default prompt configured in routing

### Phone Testing
1. Configure phone number in `customer_routing.json`
2. Deploy with `azd up` or use devtunnel for local testing
3. Call the number to test live

### Prompt Iteration Tips
- Start with clear identity and role
- Test with real conversation scenarios
- Refine based on actual call patterns
- Keep prompts focused and concise (under 500 words)
- Use specific examples for complex behaviors

## Security Considerations

⚠️ **Do NOT include in prompts**:
- Actual phone numbers or addresses (use placeholders)
- Real patient/client data
- Internal system details or credentials
- Sensitive compliance information

✅ **Do include**:
- General organization purpose
- Public-facing information
- Behavioral guidelines
- Escalation procedures

## Best Practices

- **Keep responses concise**: Aim for under 3 sentences for natural conversation flow
- **Use natural language**: Write as you would speak, including conversational phrases
- **Test changes thoroughly**: Small wording changes can significantly impact agent behavior
- **Version control**: This file is tracked in git, so you can see prompt evolution over time

## Fallback Behavior

If the prompt file is missing or unreadable, the system falls back to a basic prompt. Check server logs for warnings if the agent behaves unexpectedly.
