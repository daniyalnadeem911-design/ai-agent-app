from openai import OpenAI
from config import Config

client = OpenAI(
    api_key=Config.OPENAI_API_KEY,
    base_url=Config.OPENAI_BASE_URL
)


def chat_completion(system_prompt, user_message, max_tokens=1000, temperature=0.7):
    """Base function for all AI calls."""
    try:
        response = client.chat.completions.create(
            model=Config.AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI API Error: {e}")
        return f"AI service error: {str(e)}"


# ─── EMAIL FUNCTIONS ────────────────────────────────────────────────────────

def analyze_email(email_data):
    """
    Analyze a single email and return:
    - summary (2-3 lines)
    - urgency (low/medium/high/critical)
    - category
    - sentiment
    - action_items
    """
    system = """You are an intelligent email analyst. 
    Analyze emails and respond ONLY with valid JSON in this exact format:
    {
        "summary": "2-3 sentence summary",
        "urgency": "low|medium|high|critical",
        "category": "work|personal|finance|client|interview|promotional|spam|important",
        "sentiment": "positive|neutral|negative|urgent",
        "action_items": ["item1", "item2"],
        "needs_reply": true or false
    }
    No extra text, only JSON."""

    user_msg = f"""
    From: {email_data['sender']}
    Subject: {email_data['subject']}
    Body: {email_data['body'][:2000]}
    """

    import json
    result = chat_completion(system, user_msg, max_tokens=500, temperature=0.3)

    try:
        return json.loads(result)
    except:
        return {
            "summary": email_data['snippet'],
            "urgency": "medium",
            "category": "work",
            "sentiment": "neutral",
            "action_items": [],
            "needs_reply": False
        }


def generate_email_reply(email_data, tone_instruction, thread_context=None, user_name=None):
    sign_off = f"\n\nBest regards,\n{user_name}" if user_name else ""

    system = f"""You are an expert email writer. 
    Generate a reply email based on the user's tone instructions.
    Tone instruction: {tone_instruction}
    Write only the email body, no subject line, no metadata.
    End the email with this exact sign-off: {sign_off}
    Do not add any other name or signature."""

    context = ""
    if thread_context:
        context = f"\nPrevious thread context:\n{thread_context[:1000]}\n"

    user_msg = f"""
    {context}
    Original email from {email_data['sender']}:
    Subject: {email_data['subject']}
    Body: {email_data['body'][:2000]}

    Generate a reply following the tone instruction exactly.
    """

    return chat_completion(system, user_msg, max_tokens=800, temperature=0.7)


def generate_inbox_summary(emails):
    """Generate a daily inbox summary from list of emails."""
    if not emails:
        return "Your inbox is empty."

    system = """You are an executive assistant. 
    Create a concise daily inbox briefing. Include:
    - Total email count
    - Critical/urgent items requiring immediate attention
    - Important emails needing reply
    - Deadlines mentioned
    - Key themes
    Keep it under 300 words. Be direct and actionable."""

    email_list = ""
    for i, e in enumerate(emails[:15], 1):
        email_list += f"{i}. From: {e['sender']} | Subject: {e['subject']} | Snippet: {e['snippet'][:100]}\n"

    return chat_completion(system, f"Summarize these inbox emails:\n{email_list}", max_tokens=600)


# ─── CALENDAR FUNCTIONS ─────────────────────────────────────────────────────

def generate_event_preparation(event):
    """
    Given a calendar event, generate intelligent preparation suggestions.
    Adapts based on event type (interview, meeting, exam, gym, etc.)
    """
    system = """You are an intelligent executive assistant.
    Analyze this calendar event and generate specific, actionable preparation suggestions.

    Determine the event type from the title and description:
    - Interview → technical/behavioral prep, research company
    - Meeting → agenda prep, questions to ask, documents to review
    - Exam/Test → study topics, key concepts
    - Presentation → key points, audience analysis
    - Gym/Workout → equipment, nutrition, goals
    - Doctor → symptoms to mention, questions to ask
    - Other → relevant preparation

    Respond in this JSON format:
    {
        "event_type": "interview|meeting|exam|presentation|gym|doctor|other",
        "priority": "low|medium|high|critical",
        "preparation_steps": ["specific step 1", "step 2", "step 3"],
        "time_needed": "30 mins|1 hour|2 hours",
        "key_focus": "one-line most important thing to focus on"
    }
    Only JSON, no extra text."""

    attendee_emails = [a['email'] for a in event.get('attendees', [])]

    user_msg = f"""
    Event: {event['title']}
    Time: {event['start']}
    Description: {event.get('description', 'No description')}
    Location: {event.get('location', 'Not specified')}
    Attendees: {', '.join(attendee_emails) if attendee_emails else 'None listed'}
    """

    import json
    result = chat_completion(system, user_msg, max_tokens=600, temperature=0.4)

    try:
        return json.loads(result)
    except:
        return {
            "event_type": "other",
            "priority": "medium",
            "preparation_steps": ["Review event details", "Prepare any required materials"],
            "time_needed": "30 mins",
            "key_focus": "Be prepared and on time"
        }


def generate_meeting_briefing(event, related_emails=None):
    """
    Generate a full meeting briefing combining event details + related email history.
    """
    system = """You are an executive assistant preparing a meeting briefing.
    Combine calendar event details with email history to create a comprehensive briefing.
    Include: purpose, key people, prior context, what to prepare, potential discussion points.
    Be concise but complete. Max 400 words."""

    email_context = ""
    if related_emails:
        for e in related_emails[:3]:
            email_context += f"- Email from {e['sender']}: {e['snippet']}\n"

    user_msg = f"""
    Meeting: {event['title']}
    Time: {event['start']}
    Description: {event.get('description', '')}
    Attendees: {[a['email'] for a in event.get('attendees', [])]}

    Related email history:
    {email_context if email_context else 'No related emails found'}

    Generate a meeting briefing document.
    """

    return chat_completion(system, user_msg, max_tokens=700)


# ─── CHAT ASSISTANT ──────────────────────────────────────────────────────────

def chat_with_assistant(user_message, calendar_events=None, recent_emails=None, chat_history=None):
    """
    Main chat assistant function with full context awareness.
    """
    # Build context string
    context = "You are an intelligent personal executive assistant.\n\n"

    if calendar_events:
        context += "UPCOMING CALENDAR EVENTS:\n"
        for e in calendar_events[:5]:
            context += f"- {e['title']} at {e['start']}\n"
        context += "\n"

    if recent_emails:
        context += "RECENT INBOX EMAILS:\n"
        for e in recent_emails[:5]:
            context += f"- From {e['sender']}: {e['subject']}\n"
        context += "\n"

    context += """Answer questions about emails and calendar intelligently.
    You can: summarize emails, prepare meeting briefs, draft replies, identify urgent tasks.
    Be direct, specific, and actionable."""

    # Build conversation history
    messages = [{"role": "system", "content": context}]

    if chat_history:
        for msg in chat_history[-6:]:  # Keep last 6 exchanges for context
            messages.append(msg)

    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=Config.AI_MODEL,
            messages=messages,
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Assistant error: {str(e)}"