# app/services.py

import json
import logging
from openai import OpenAI, APIError
from app.models import ProductInput, ProductCardOutput
from app.prompt import SYSTEM_PROMPT
from app.config import Settings

logger = logging.getLogger(__name__)

def normalize_input(data: ProductInput) -> dict:
    """Нормализация входных данных"""

    normalized = data.model_dump()
    if not normalized.get("description"):
        normalized["description"] = "данных нет"
    if not normalized.get("specs"):
        normalized["specs"] = {"данных нет": "нет"}
    return normalized


def _validate_and_fix_output(result: dict, original_data: dict) -> dict:
    """
    Валидация ответа LLM. Гарантирует соблюдение бизнес-требований, 
    с которыми LLM часто не справляется (подсчет символов, проверка заглушек).
    """

    # Гарантия длины заголовка (для SEO-title)
    if len(result["seo_title"]) > 70:
        result["seo_title"] = result["seo_title"][:67] + "..."

    # Проверка commercial_block на заглушки
    bad_phrases = ["коммерческий блок", "текст для менеджера", "данных нет"]

    if any(phrase in result["commercial_block"].lower() for phrase in bad_phrases):
        name = original_data.get('name', 'Данное оборудование')
        manufacturer = original_data.get('manufacturer', 'производителя')
        
        result["commercial_block"] = (
            f"{name} от компании {manufacturer} предназначено для надежной эксплуатации "
            f"в составе промышленных и технических систем. Оно решает задачи по обеспечению "
            f"стабильной работы инфраструктуры, контролю или автоматизации процессов. "
            f"Продукт ориентирован на технических специалистов, монтажные организации и отделы закупок, "
            f"ищущие проверенные и отказоустойчивые B2B-решения."
        )

    # Проверка длины SEO-описания
    desc_len = len(result["seo_description"])

    if desc_len < 800:
        # дополняем описание стандартным B2B-блоком
        result["seo_description"] += (
            " Оборудование проходит строгий контроль качества и соответствует отраслевым стандартам. "
            "Использование данного решения позволяет оптимизировать технологические процессы, "
            "снизить риски простоев и обеспечить стабильный обмен информацией между узлами системы. "
            "Для получения индивидуального коммерческого предложения, уточнения сроков поставки "
            "и условий гарантийного обслуживания, пожалуйста, свяжитесь с нашими специалистами."
        )

    # Проверка missing_data_warning
    specs_count = len(original_data.get("specs", {}))

    if result["missing_data_warning"] in ["", "Нет"] and specs_count < 4:
        result["missing_data_warning"] = (
            "Входных данных недостаточно для полноценной B2B-карточки. "
            "Рекомендуется добавить: напряжение питания, габаритные размеры, степень защиты (IP) и условия эксплуатации."
        )

    return result


def generate_mock_response(data: dict) -> dict:
    """Генерирует тестовый ответ"""
    pass 


def generate_card(data: ProductInput, settings: Settings) -> ProductCardOutput:
    """Генерация карточки"""

    normalized = normalize_input(data)

    if settings.use_mock or settings.openai_api_key in ("your_api_key_here", ""):
        logger.warning("Используется демо-режим (mock response)")
        return ProductCardOutput(**generate_mock_response(normalized))

    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url
    )

    try:
        response = client.beta.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Сформируй карточку для товара: {json.dumps(normalized, ensure_ascii=False)}"}
            ],
            response_format=ProductCardOutput,
        )
        raw_result = response.choices[0].message.parsed.model_dump()
        
        # Валидируем данные
        validated_result = _validate_and_fix_output(raw_result, normalized)
        
        return ProductCardOutput(**validated_result)
        
    except APIError as e:
        logger.error(f"Ошибка OpenAI API: {e}")
        raise
