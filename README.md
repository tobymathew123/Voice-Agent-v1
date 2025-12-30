# AI Voice Agent for Indian BFSI Sector

A production-ready real-time voice agent system designed for the Banking, Financial Services, and Insurance (BFSI) sector in India. This system handles both inbound and outbound calls over PSTN, integrating speech processing with AI-powered conversation capabilities while maintaining strict safety and compliance standards.

---

## Project Overview

### What It Does

This voice agent system enables automated, intelligent phone conversations for BFSI organizations. It handles customer service inquiries, delivers notifications, and conducts marketing campaigns through natural voice interactions over traditional phone lines.

### Problem It Solves

BFSI organizations in India face challenges in scaling customer support and outreach while maintaining quality and compliance. Manual call handling is expensive and inconsistent, while existing IVR systems provide poor user experiences. This system bridges the gap by providing:

- **Natural conversations** through AI-powered agents instead of rigid menu trees
- **24/7 availability** without human agent costs
- **Compliance-first design** that never requests sensitive information
- **Scalable outreach** for notifications and campaigns
- **Multilingual readiness** for India's diverse linguistic landscape

### Why Voice Agents in BFSI Matter

The BFSI sector handles millions of customer interactions daily—account inquiries, transaction alerts, loan applications, policy information, and more. Voice agents can:

- Reduce call center operational costs by 60-70%
- Provide instant responses without wait times
- Maintain consistent quality across all interactions
- Scale during peak periods without additional staffing
- Deliver personalized experiences using customer context

### System Summary

This system integrates Vobiz.ai for PSTN telephony, Deepgram for real-time speech processing (STT/TTS), and LangChain with OpenAI GPT-4 for intelligent conversation management. Built on FastAPI, it provides a clean, modular architecture with proper separation between telephony, speech, and AI layers. The system supports incoming customer service calls, outbound notifications (OTP delivery, alerts), and marketing campaigns with structured data capture and analytics.

---

## Key Features

### Incoming Call Handling (PSTN)
- Receives calls via Vobiz.ai telephony platform
- Real-time speech-to-text transcription using Deepgram
- AI-powered conversation with context retention
- Text-to-speech responses in Indian English
- Session management with conversation history
- Graceful error handling and fallback mechanisms

### Outbound Call Capabilities
- **Notification Calls**: OTP delivery, transaction alerts, payment reminders
- **Marketing Calls**: Campaign-based outreach with interest capture
- Programmable call initiation via REST API
- Campaign metadata tracking
- User response classification (interested/not interested/maybe)

### Real-Time Speech Processing
- **STT**: Deepgram Nova-2 model with Indian English (en-IN) support
- **TTS**: Telephony-compatible audio (μ-law, 8kHz, mono)
- Audio caching for reduced latency
- Text sanitization for Indian context (OTP → O T P, Rs. → Rupees)
- Async processing for low-latency responses

### AI-Powered Conversations
- LangChain agent with ReAct reasoning
- OpenAI GPT-4 for natural language understanding
- Per-session conversation memory
- Three BFSI personas: Bank, Insurance, Financial Services
- Tool calling for branch lookup, product information, transfers
- Context-aware responses

### Campaign & Data Handling
- Structured data capture for marketing calls
- User interest extraction from natural language
- CSV storage for campaign analytics
- Call metrics tracking (duration, cost, outcomes)
- Daily summary generation
- Privacy-compliant design (no PII storage)

### Metrics & Logging
- Comprehensive call metrics (ring time, talk time, total duration)
- Call cost tracking from CDR data
- Quality metrics (user turns, agent turns, transcripts)
- Daily and campaign-level analytics
- Thread-safe CSV storage
- Detailed logging for debugging

### Multilingual-Ready Design
- Language configurable per call
- Voice selection per language
- Text sanitization rules per locale
- Extensible to Hindi, Tamil, Malayalam, and other Indian languages
- Currently optimized for Indian English

---

## System Architecture

### Component Overview

The system follows a clean, layered architecture with clear separation of concerns:

**Telephony Layer** handles all phone call interactions through Vobiz.ai. It receives webhooks for incoming calls, manages call state, and generates XML responses to control call flow. This layer knows nothing about AI or speech processing—it simply coordinates the conversation flow.

**Speech Processing Layer** manages all audio transformations. Deepgram STT converts caller speech to text in real-time, while Deepgram TTS generates natural-sounding responses in telephony-compatible formats. An abstraction layer (Speech Processor) decouples telephony from Deepgram specifics, allowing easy provider swapping.

**AI Agent Layer** powers intelligent conversations using LangChain and OpenAI GPT-4. It maintains per-session conversation memory, performs ReAct-style reasoning, and calls tools for information retrieval. The agent is completely isolated from telephony concerns—it receives text input and returns text responses.

**Data Storage Layer** persists call records, metrics, and campaign data using thread-safe CSV files. This provides simple, reliable storage suitable for initial deployment, with a clear path to database migration for scale.

**API Layer** exposes REST endpoints for outbound call initiation, analytics queries, and system monitoring. Built on FastAPI, it provides automatic API documentation and async request handling.

### Technology Integration

**Vobiz.ai** serves as the telephony provider, handling PSTN connectivity, call routing, and webhook delivery. It supports TwiML-compatible XML for call control, making it straightforward to implement complex call flows.

**Deepgram** provides production-grade speech services. The Nova-2 STT model delivers accurate transcription for Indian English accents, while the TTS service generates clear, natural audio optimized for phone calls. Both services are accessed asynchronously for minimal latency.

**LangChain + OpenAI** power the conversational AI. LangChain provides the agent framework with memory management and tool calling, while GPT-4 handles natural language understanding and generation. The combination enables context-aware, multi-turn conversations.

**FastAPI** serves as the backend framework, chosen for its async capabilities, automatic API documentation, and excellent performance. It handles webhook processing, API requests, and serves generated audio files.

### Separation of Concerns

The architecture maintains strict boundaries between layers:

- Telephony code imports zero AI modules
- AI agent imports zero telephony modules  
- Speech processing is accessed only through abstraction functions
- Data models are shared but logic is isolated

This design allows independent testing, easy component replacement, and clear reasoning about system behavior.

---

## Technology Stack

### Backend Framework
- **FastAPI** (Python 3.10+): Async web framework with automatic API documentation
- **Uvicorn**: ASGI server for production deployment
- **Pydantic**: Data validation and settings management

### Telephony Provider
- **Vobiz.ai**: PSTN/SIP telephony platform with TwiML-compatible API
- **REST API**: Outbound call initiation and management
- **Webhooks**: Real-time call event delivery

### Speech Services
- **Deepgram STT**: Nova-2 model for Indian English transcription
- **Deepgram TTS**: Aura voices with telephony audio format (μ-law, 8kHz)
- **Audio Processing**: Python audioop for format conversion

### LLM Provider
- **OpenAI GPT-4**: Primary language model for conversation
- **LangChain**: Agent framework with ReAct reasoning and tool calling
- **ConversationBufferMemory**: Per-session conversation history

### Hosting Platform
- **Render.com**: Recommended deployment platform with automatic HTTPS
- **Alternative**: Heroku, Railway, AWS, Google Cloud Run, or any Python-compatible host
- **Requirements**: Public HTTPS endpoint for webhook delivery

### Data Storage
- **CSV Files**: Thread-safe storage for metrics and campaign data
- **In-Memory**: Session state and conversation history
- **Future**: PostgreSQL or MongoDB for production scale

---

## Call Flows

### Inbound Call Flow

1. **Call Initiation**: Customer dials the Vobiz DID (phone number)
2. **Webhook Delivery**: Vobiz sends POST request to `/telephony/incoming` with call details
3. **Session Creation**: System creates in-memory session with call ID and metadata
4. **Welcome Message**: TTS generates greeting audio, system returns XML with `<Play>` tag
5. **Audio Playback**: Vobiz plays welcome message to caller
6. **Speech Gathering**: XML includes `<Gather>` to capture caller's speech
7. **User Speaks**: Caller responds to greeting
8. **Speech Transcription**: Vobiz sends speech to `/telephony/gather/{call_id}` endpoint
9. **AI Processing**: LangChain agent processes transcribed text with conversation context
10. **Response Generation**: Agent returns appropriate response text
11. **TTS Synthesis**: System generates audio response (cached if previously generated)
12. **Response Delivery**: XML returns `<Play>` with response audio URL
13. **Conversation Loop**: Steps 7-12 repeat for multi-turn conversation
14. **Call Termination**: User hangs up or system sends `<Hangup>` XML
15. **Metrics Capture**: System calculates and saves call metrics (duration, cost, quality)
16. **Session Cleanup**: In-memory session data cleared

### Outbound Notification Call Flow

1. **API Request**: System receives POST to `/telephony/outbound/notification` with recipient number and message
2. **Call Initiation**: Vobiz API called to start outbound call
3. **Call Answered**: Vobiz sends webhook to `/telephony/outbound/notification/handle`
4. **Session Creation**: System creates session with notification metadata
5. **AI Message Generation**: Agent generates natural delivery message from notification content
6. **TTS Synthesis**: Message converted to audio
7. **Message Delivery**: XML returns `<Say>` or `<Play>` with notification
8. **Confirmation**: Optional acknowledgment gathering
9. **Call End**: System sends `<Hangup>` after delivery
10. **Data Capture**: Delivery status saved (delivered/acknowledged)

### Marketing Call Flow

1. **API Request**: POST to `/telephony/outbound/marketing` with campaign details
2. **Call Initiation**: Vobiz API starts call with campaign metadata
3. **Call Answered**: Webhook to `/telephony/outbound/marketing/handle`
4. **Session Creation**: System creates session with campaign context
5. **AI Pitch Generation**: Agent generates personalized marketing message based on campaign objective and target segment
6. **Message Delivery**: TTS plays marketing pitch
7. **Interest Gathering**: XML includes `<Gather>` for user response
8. **User Response**: Caller indicates interest level (yes/no/maybe)
9. **Interest Extraction**: Natural language processing classifies response
10. **Follow-up**: Agent generates appropriate follow-up based on interest
11. **Data Capture**: User interest, call duration, and campaign metadata saved to CSV
12. **Call End**: System thanks caller and ends call
13. **Analytics Update**: Campaign statistics recalculated

---

## Safety & Compliance Considerations

### BFSI Regulatory Constraints

The system is designed with financial sector compliance in mind:

- **No Credential Requests**: Agent never asks for passwords, PINs, OTPs, account numbers, or CVV codes
- **No Financial Advice**: Agent does not provide investment recommendations or financial guidance
- **No Promises**: Agent cannot approve loans, open accounts, or make binding commitments
- **Secure Channel Redirection**: For sensitive operations, agent directs users to secure channels (mobile app, branch visit, verified hotline)

### Privacy & Data Protection

- **Phone Number Hashing**: Caller numbers hashed before storage for privacy
- **No PII Storage**: System does not store names, addresses, or personal identifiers
- **Conversation Logging**: Transcripts stored only for active sessions, cleared on call end
- **Aggregated Analytics**: Only campaign-level statistics retained, not individual responses

### Safe Failure Responses

The agent includes safety guardrails:

- **Sensitive Info Detection**: If user volunteers sensitive information, agent politely redirects
- **Unknown Intent Handling**: For unclear requests, agent asks for clarification rather than guessing
- **Error Graceful Degradation**: If AI fails, system falls back to simple XML `<Say>` responses
- **Timeout Management**: Calls automatically end after reasonable inactivity to prevent resource waste

### Prompt Engineering for Safety

Agent prompts explicitly instruct:
- Never request sensitive information
- Acknowledge limitations and redirect appropriately
- Maintain professional, helpful tone
- Keep responses concise for voice delivery (2-3 sentences)
- Use simple language suitable for phone conversations

---

## Configuration & Deployment

### Environment Variables

The system requires the following environment variables (configured in `.env` file):

**Server Configuration:**
- `HOST`: Server bind address (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `ENVIRONMENT`: Deployment environment (development/production)

**Vobiz.ai Configuration:**
- `VOBIZ_AUTH_ID`: Vobiz account authentication ID
- `VOBIZ_AUTH_TOKEN`: Vobiz API authentication token
- `VOBIZ_API_URL`: Vobiz API base URL (default: https://api.vobiz.ai)

**Deepgram Configuration:**
- `DEEPGRAM_API_KEY`: Deepgram API key for STT/TTS services

**OpenAI Configuration:**
- `OPENAI_API_KEY`: OpenAI API key for GPT-4 access
- `OPENAI_MODEL`: Model name (default: gpt-4)

**Optional Configuration:**
- `LOG_LEVEL`: Logging verbosity (default: INFO)
- `DATABASE_URL`: Future database connection string

### Deployment Platform (Render)

**Recommended Setup:**

1. **Repository Connection**: Connect GitHub repository to Render
2. **Service Type**: Web Service
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `python -m app.main`
5. **Environment**: Python 3.10 or higher
6. **Environment Variables**: Configure all required variables in Render dashboard

**Automatic Features:**
- HTTPS certificate provisioned automatically
- Health check endpoint: `/health/`
- Auto-restart on crashes
- Deployment logs and monitoring

**Public URL**: Render assigns URL like `https://your-app-name.onrender.com`

### Webhook Configuration

**In Vobiz.ai Dashboard:**

1. Navigate to Phone Numbers / DIDs section
2. Select your purchased phone number
3. Configure Voice URL: `https://your-app-name.onrender.com/telephony/incoming`
4. Set HTTP Method: POST
5. Configure Status Callback: `https://your-app-name.onrender.com/telephony/events`
6. Set Status Callback Method: POST

**Webhook Endpoints:**
- `/telephony/incoming`: Inbound call handler
- `/telephony/gather/{call_id}`: Speech input handler
- `/telephony/events`: Call status events
- `/telephony/outbound/notification/handle`: Notification call handler
- `/telephony/outbound/marketing/handle`: Marketing call handler

### Public HTTPS Requirement

Vobiz.ai requires HTTPS for webhook delivery. Options:

- **Render**: Automatic HTTPS (recommended)
- **Heroku**: Automatic HTTPS
- **Custom Server**: Configure SSL certificate (Let's Encrypt recommended)
- **Development**: Use ngrok or localtunnel for testing

---

## Testing Strategy

### Inbound Call Testing

**Prerequisites:**
- Server deployed to public HTTPS URL
- Vobiz DID configured with webhook URL
- Test phone available

**Test Procedure:**
1. Call the Vobiz DID from test phone
2. Verify welcome message plays
3. Speak a test query (e.g., "I need help with my account")
4. Verify AI response is relevant and natural
5. Continue conversation for 2-3 turns
6. Check server logs for session creation, STT transcription, agent processing
7. Verify metrics saved after call ends

**Success Criteria:**
- Call connects without errors
- Speech transcription accurate
- AI responses contextually appropriate
- Audio quality clear
- No crashes or timeouts

### Outbound Call Testing

**Notification Call Test:**
```bash
curl -X POST "https://your-app.onrender.com/telephony/outbound/notification" \
  -H "Content-Type: application/json" \
  -d '{
    "to_number": "+919876543210",
    "notification_type": "test",
    "message": "This is a test notification",
    "priority": "normal"
  }'
```

**Verify:**
- Call initiated successfully (check API response for call_sid)
- Test phone receives call
- Notification message delivered clearly
- Call ends gracefully
- Delivery status captured

**Marketing Call Test:**
```bash
curl -X POST "https://your-app.onrender.com/telephony/outbound/marketing" \
  -H "Content-Type: application/json" \
  -d '{
    "to_number": "+919876543210",
    "campaign_id": "TEST001",
    "campaign_name": "Test Campaign",
    "segment": "test_users",
    "objective": "testing"
  }'
```

**Verify:**
- Call initiated
- Marketing message delivered
- User response captured
- Interest classification correct
- Data saved to CSV

### Speech Pipeline Validation

**Run Test Suite:**
```bash
python test_speech.py
```

**Validates:**
- TTS audio generation (3 test cases)
- Audio format validation (μ-law, 8kHz, mono)
- Text sanitization (Indian context)
- Audio caching functionality

**Expected Output:**
```
✓ TTS Generation (3/3 tests passed)
✓ Text Sanitization (3/3 tests passed)
✓ Audio Validation (3/3 tests passed)
```

### Agent Behavior Validation

**Run Test Suite:**
```bash
python test_agent.py
```

**Validates:**
- All three personas (Bank, Insurance, Financial Services)
- Conversation memory across turns
- Safety guardrails (no sensitive info requests)
- Tool calling (branch lookup, product info)
- Notification and marketing message generation

**Expected Output:**
```
✓ Bank Persona (1/1 test)
✓ Insurance Persona (1/1 test)
✓ Financial Services Persona (1/1 test)
✓ Conversation Memory (5/5 turns)
✓ Safety Guardrails (4/4 tests)
✓ Tool Usage (3/3 tools)
```

---

## Assumptions & Limitations

### Real-Time Latency Constraints

The system is designed for phone conversations where latency matters:

- **TTS Cached**: ~10ms response time
- **TTS Uncached**: ~500-1000ms (Deepgram API)
- **STT Streaming**: Real-time transcription
- **Agent Processing**: ~200-500ms (OpenAI API)

Total response time typically 1-2 seconds, acceptable for natural conversation flow.

### Managed LLM Usage

The system uses OpenAI's hosted GPT-4 API:

- **No local LLM**: Relies on external API availability
- **API costs**: Per-token pricing applies
- **Rate limits**: Subject to OpenAI account limits
- **Internet dependency**: Requires stable connection

This trade-off prioritizes quality and development speed over complete control.

### RAG Validation Handled Separately

The current implementation does NOT include Retrieval-Augmented Generation (RAG):

- **No vector database**: No FAISS, Chroma, or Pinecone integration
- **No embeddings**: No document retrieval
- **No knowledge base**: Agent relies on GPT-4's training data

RAG can be added later for domain-specific knowledge (product catalogs, policy documents, FAQs).

### No Production Database

Current data storage uses CSV files:

- **Session state**: In-memory only (lost on restart)
- **Call metrics**: CSV files (thread-safe but not scalable)
- **Campaign data**: CSV files

This is suitable for initial deployment and testing. Production deployment should migrate to PostgreSQL or MongoDB for:
- Persistent session storage
- Efficient querying
- Concurrent access
- Data integrity

### Phone Number Management

- **Inbound DIDs**: Managed in Vobiz dashboard, not in code
- **Outbound Caller ID**: Passed per API call, no default configured
- **Number Format**: E.164 format required (+[country][area][number])

### Audio Format Constraints

- **PSTN Standard**: μ-law encoding at 8kHz sample rate
- **Mono Channel**: Single audio channel only
- **WAV Container**: Used for compatibility

These constraints are telephony standards, not system limitations.

---

## Future Enhancements

### Admin Dashboard
- Web UI for campaign management
- Real-time call monitoring
- Analytics visualization (charts, graphs)
- User management and access control
- Export functionality (CSV, Excel, PDF)

### Advanced Analytics
- Conversation sentiment analysis
- Call quality scoring
- Agent performance metrics
- A/B testing for prompts and voices
- Conversion funnel tracking
- Predictive analytics for campaign optimization

### Expanded Multilingual Support
- Hindi language support with native voices
- Tamil, Telugu, Malayalam, Kannada support
- Automatic language detection
- Code-switching handling (Hinglish)
- Regional accent optimization

### Optional RAG Integration
- Product catalog retrieval
- Policy document search
- FAQ knowledge base
- Real-time data integration (account balances, transaction history)
- Hybrid approach: RAG for facts, LLM for conversation

### Infrastructure Improvements
- Database migration (PostgreSQL)
- Redis for session caching
- Message queue for async processing (Celery, RabbitMQ)
- Horizontal scaling with load balancer
- CDN for audio file delivery
- Webhook signature verification
- Rate limiting and DDoS protection

### Enhanced Features
- Call recording storage and playback
- Live agent transfer capability
- Scheduled callback system
- Multi-channel support (SMS, WhatsApp)
- CRM integration (Salesforce, HubSpot)
- Compliance reporting and audit logs

---

## License / Academic Note

This project was developed as an academic learning exercise to explore the integration of modern AI and telephony technologies for the BFSI sector. It demonstrates:

- Real-time speech processing integration
- AI agent design for domain-specific applications
- Production-grade API development
- Telephony system architecture
- Safety-first design for sensitive domains

**Academic Purpose**: This system is designed for educational and demonstration purposes. It showcases technical capabilities and architectural patterns suitable for BFSI voice agents.

**Not for Commercial Deployment**: This codebase has not undergone the extensive security audits, compliance certifications, and production hardening required for commercial BFSI deployment. Organizations considering similar systems should:

- Conduct thorough security audits
- Obtain necessary regulatory approvals
- Implement comprehensive logging and monitoring
- Add database persistence and redundancy
- Establish disaster recovery procedures
- Comply with data protection regulations (GDPR, Indian IT Act)

**Learning Outcomes**: This project demonstrates proficiency in:
- Async Python development (FastAPI)
- Third-party API integration (Vobiz, Deepgram, OpenAI)
- LangChain agent development
- System architecture and design patterns
- Testing and validation strategies
- Documentation and code organization

---

## Getting Started

### Prerequisites
- Python 3.10 or higher
- Vobiz.ai account with purchased DID
- Deepgram API key
- OpenAI API key with GPT-4 access

### Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and configure environment variables
4. Run locally: `python -m app.main`
5. Access API docs: `http://localhost:8000/docs`

### Quick Test

```bash
# Check health
curl http://localhost:8000/health/

# View API documentation
open http://localhost:8000/docs
```

For detailed deployment instructions, see the Configuration & Deployment section above.

---

**Built with FastAPI, LangChain, Deepgram, and OpenAI**  
**Designed for the Indian BFSI Sector**
