import anthropic
import base64
import json
import config

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


async def extract_passport_data(photo_bytes: bytes) -> dict:
    """
    Отправляет фото паспорта в Claude Vision и извлекает данные.
    Возвращает словарь с полями: full_name, birth_date, passport_number, pinfl, address
    """
    image_data = base64.standard_b64encode(photo_bytes).decode("utf-8")

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": """Это фото паспорта. Извлеки следующие данные и верни ТОЛЬКО JSON без лишнего текста:
{
  "full_name": "Фамилия Имя Отчество (полностью)",
  "birth_date": "ДД.ММ.ГГГГ",
  "passport_number": "серия и номер паспорта (например AA1234567)",
  "pinfl": "14-значный ПИНФЛ",
  "address": "адрес прописки"
}
Если какое-то поле не найдено или нечитаемо — оставь пустую строку "".
Верни ТОЛЬКО JSON, никакого другого текста."""
                    }
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    # Убираем возможные markdown-обёртки
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {
            "full_name": "",
            "birth_date": "",
            "passport_number": "",
            "pinfl": "",
            "address": ""
        }

    return data
