# app/services.py

import json
import logging
from openai import OpenAI, APIError

from app.models import ProductInput, ProductCardOutput
from app.prompt import SYSTEM_PROMPT
from app.config import Settings

logger = logging.getLogger(__name__)

def normalize_input(data: ProductInput) -> dict:
    """Заменяет пустые значения на 'данных нет' для явной передачи в LLM"""
    normalized = data.model_dump()
    if not normalized.get("description"):
        normalized["description"] = "данных нет"
    if not normalized.get("specs"):
        normalized["specs"] = {"данных нет": "нет"}
    return normalized

def generate_mock_response(data: dict) -> dict:
    """Демо-ответ для запуска без API-ключа"""
    missing = []
    if data.get("description") in (None, "", "данных нет"):
        missing.append("Текстовое описание")
    if not data.get("specs") or data["specs"].get("данных нет"):
        missing.append("Технические характеристики")
    if data.get("manufacturer") in (None, "", "данных нет"):
        missing.append("Производитель")

    warning = "Нет" if not missing else f"Критически отсутствуют: {', '.join(missing)}"

    return {
        "seo_title": f"{data.get('manufacturer', '')} {data.get('name', '')}".strip()[:70] or "данных нет",
        "seo_description": "Детальное описание отсутствует во входных данных. Свяжитесь с менеджером для уточнения характеристик.",
        "key_specs": [f"{k}: {v}" for k, v in list(data.get("specs", {}).items())[:6]] or ["данных нет"],
        "search_queries": [f"купить {data.get('name', '')}"] if data.get("name") else ["данных нет"],
        "commercial_block": "данных нет для формирования коммерческого предложения" if not data.get("description") or data["description"] == "данных нет" else "Подходит для интеграции в системы автоматизации.",
        "missing_data_warning": warning
    }

def generate_card(data: ProductInput, settings: Settings) -> ProductCardOutput:
    normalized = normalize_input(data)

    # Мок-режим: если ключа нет или явно включен флаг
    if settings.use_mock or settings.openai_api_key in ("your_api_key_here", ""):
        logger.warning("Используется демо-режим (mock response)")
        return ProductCardOutput(**generate_mock_response(normalized))

    client = OpenAI(api_key=settings.openai_api_key)

    try:
        response = client.beta.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Сформируй карточку для товара: {json.dumps(normalized, ensure_ascii=False)}"}
            ],
            response_format=ProductCardOutput,
        )
        return response.choices[0].message.parsed
    except APIError as e:
        logger.error(f"Ошибка OpenAI API: {e}")
        raise
