# app/models.py

from pydantic import BaseModel, Field
from typing import List, Optional

# ===== Входные данные (Request) =====
class ProductInput(BaseModel):
    name: Optional[str] = Field(default="данных нет", description="Название товара")
    manufacturer: Optional[str] = Field(default="данных нет", description="Производитель")
    specs: Optional[dict] = Field(default_factory=dict, description="Технические характеристики")
    description: Optional[str] = Field(default="данных нет", description="Текстовое описание")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "МК110-224.8Д.4Р [М01]",
                    "manufacturer": "ОВЕН",
                    "specs": {
                        "Тип": "Комбинированный модуль ввода-вывода",
                        "Интерфейс": "RS-485"
                    },
                    "description": "Модуль для сбора данных и управления..."
                }
            ]
        }
    }

# ===== Выходные данные (Response) =====
class ProductCardOutput(BaseModel):
    seo_title: str = Field(..., description="SEO-заголовок до 70 символов")
    seo_description: str = Field(..., description="SEO-описание 800-1200 символов")
    key_specs: List[str] = Field(..., description="Список ключевых характеристик (до 6)")
    search_queries: List[str] = Field(..., description="3-5 поисковых запросов")
    commercial_block: str = Field(..., description="Коммерческий блок для менеджера")
    missing_data_warning: str = Field(..., description="Предупреждение о недостающих данных или 'Нет'")

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
