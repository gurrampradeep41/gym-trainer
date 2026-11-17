import sys
from ai_service import get_groq_client, get_groq_model


def check_groq_connection():
    try:
        model = get_groq_model()
        client = get_groq_client()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": "Give me three beginner gym training tips."
                }
            ],
            temperature=0.3,
            max_tokens=300
        )

        choices = getattr(response, "choices", None)
        content = choices[0].message.content if choices and choices[0].message else None

        if not content:
            raise RuntimeError("Groq returned an empty response.")

        print(f"GROQ CONNECTION SUCCESSFUL (Model: {model})")
        print(content.strip())
        return True

    except Exception as error:
        print("GROQ CONNECTION FAILED")
        print(str(error))
        return False


if __name__ == "__main__":
    success = check_groq_connection()
    sys.exit(0 if success else 1)