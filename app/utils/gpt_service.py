import os
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def load_profile(path="app/knowledge/profile.md") -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def generate_reply(user_text: str, profile_text: str) -> str:
    system_prompt = (
        "Ты — голосовой ассистент от лица Хонгора. "
        "Отвечай кратко, дружелюбно и по существу. "
        "Вот информация о нём:\n\n"
        f"{profile_text}"
    )

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            max_tokens=200,
            temperature=0.7,
        )
        return completion.choices[0].message["content"]
    except Exception as e:
        print("❌ Ошибка от GPT:", e)
        return "Извините, произошла ошибка при генерации ответа."
