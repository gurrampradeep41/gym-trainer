# ==========================================================
# FITPRO - PHASE 7
# GROQ AI SERVICE
# ==========================================================

import os
import json

import streamlit as st
from groq import Groq

from config import get_setting
from services import verify_trainer


SYSTEM_PROMPT = """
You are FITPRO AI, an assistant for a professional gym trainer.

Your responsibilities:
1. Help trainers draft workout plans.
2. Help trainers draft nutrition plans.
3. Analyze recorded fitness progress.
4. Explain general fitness concepts.
5. Suggest practical and safe fitness improvements.
6. Summarize client fitness records.

IMPORTANT RULES:

- You assist the trainer. You do not replace professional judgment.
- Never diagnose diseases or medical conditions.
- Never prescribe medication or medical treatment.
- Do not recommend steroids or dangerous supplements.
- Do not recommend extreme calorie restriction.
- Do not guarantee weight loss or muscle gain.
- Consider age, training experience, goals and available records.
- Clearly identify missing information.
- Do not invent client measurements or progress data.
- Distinguish recorded facts from AI suggestions.
- Use simple, professional language.
- For nutrition, state that targets are estimates and require
  appropriate professional review.
- If a request involves injury, illness, pregnancy, eating
  disorders or other medical concerns, recommend evaluation
  by an appropriately qualified healthcare professional.
- Never claim that an AI-generated plan has been approved
  by the trainer.
"""


def _get_setting(name, default=""):
    value = get_setting(name, None)
    if value:
        return str(value).strip()

    try:
        secret_val = st.secrets.get(name, None)
        if secret_val:
            return str(secret_val).strip()
    except Exception:
        pass

    return os.getenv(name, default).strip()


def get_groq_client():
    api_key = _get_setting("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "Groq API key is missing. Configure GROQ_API_KEY "
            "in Streamlit secrets or environment variables."
        )

    return Groq(
        api_key=api_key,
        timeout=45.0,
        max_retries=2
    )


def get_groq_model():
    return _get_setting(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile"
    )


def generate_ai_response(
    trainer_user_id,
    task,
    client_context=None,
    question=""
):
    # Every AI request must be made by an active trainer.
    verify_trainer(trainer_user_id)

    allowed_tasks = {
        "workout_plan",
        "diet_plan",
        "progress_analysis",
        "fitness_recommendations",
        "client_summary",
        "general_chat"
    }

    if task not in allowed_tasks:
        raise ValueError("Invalid AI task.")

    question = str(question or "").strip()

    if task == "general_chat" and not question:
        raise ValueError("Please enter a question for FITPRO AI.")

    if len(question) > 5000:
        raise ValueError("Your prompt is too long (maximum 5000 characters).")

    if client_context is not None:
        if not isinstance(client_context, dict):
            raise ValueError("Invalid client context.")

        context_json = json.dumps(
            client_context,
            ensure_ascii=False,
            default=str
        )

        if len(context_json) > 15000:
            raise ValueError("Client context is too large.")
    else:
        context_json = "{}"

    task_instructions = {
        "workout_plan": """
Create a practical workout plan draft.

Include:
- Fitness goal
- Training experience
- Weekly schedule
- Exercises
- Sets and repetitions
- Rest intervals
- Warm-up and cool-down
- Progression suggestions
- Safety considerations

Do not invent unavailable client information.
""",

        "diet_plan": """
Create a nutrition plan draft.

Include:
- Estimated daily calorie target, only if sufficient
  information is available
- Protein, carbohydrate and fat considerations
- Breakfast
- Mid-morning snack
- Lunch
- Evening snack
- Dinner
- Food alternatives
- Hydration guidance
- Professional review notes

Do not present calorie calculations as medically precise.
Do not invent allergies or dietary preferences.
""",

        "progress_analysis": """
Analyze the supplied recorded progress.

Include:
- Starting versus latest recorded weight
- Weight changes
- Available BMI history
- Measurement trends
- Positive observations
- Missing information
- Questions the trainer should investigate
- Suggested next steps

Do not assume a weight change is automatically good or bad.
""",

        "fitness_recommendations": """
Provide practical fitness recommendations based on the
supplied client information.

Separate:
- Recorded facts
- Possible interpretations
- Suggestions for trainer review
- Missing information
- Safety considerations
""",

        "client_summary": """
Create a professional client progress summary.

Use these headings:
- Client overview (only supplied information)
- Fitness goal
- Weight progress
- Workout plan
- Nutrition plan
- Progress observations
- Trainer action points
- Missing information
""",

        "general_chat": """
Answer the trainer's question clearly and professionally.
If the question is unrelated to fitness management,
explain that FITPRO AI is designed for trainer assistance.
"""
    }

    user_message = f"""
TASK:
{task_instructions[task]}

RECORDED CLIENT CONTEXT:
{context_json}

TRAINER REQUEST:
{question if question else "No additional instructions provided."}

Remember:
- Use only the provided client data.
- Do not invent missing facts.
- This is a draft for trainer review.
"""

    client = get_groq_client()

    response = client.chat.completions.create(
        model=get_groq_model(),
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        temperature=0.3,
        max_tokens=1800
    )

    choices = getattr(response, "choices", None)
    if not choices or not choices[0].message or not choices[0].message.content:
        raise RuntimeError("The AI returned an empty response.")

    return choices[0].message.content.strip()