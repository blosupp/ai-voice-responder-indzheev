from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_profile(path="app/knowledge/profile.md") -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def generate_reply(user_text: str, profile_text: str) -> str:
    system_prompt = (
        "Ты — голосовой ассистент от имени Хонгора. "
        "Вот информация о нём:\n\n" + profile_text
    )
    try:
        chat = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=0.7,
            max_tokens=200
        )
        return chat.choices[0].message.content
    except Exception as e:
        print("❌ Ошибка от GPT:", e)
        return "Извините, произошла ошибка при генерации ответа."
