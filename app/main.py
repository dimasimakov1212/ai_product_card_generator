# app/main.py

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from openai import APIError

from app.config import Settings, get_settings
from app.models import ProductInput, ProductCardOutput, ErrorResponse
from app.services import generate_card

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    mode = "MOCK" if settings.use_mock or settings.openai_api_key == "your_api_key_here" else "LIVE"
    logger.info(f"🚀 Сервис запущен. Режим: {mode}, модель: {settings.openai_model}")
    yield
    logger.info("👋 Сервис остановлен")

app = FastAPI(
    title="AI-генератор карточек товаров (B2B)",
    description="Сервис формирует структурированные черновики карточек товаров для B2B-магазина на основе технических данных.",
    version="1.0.0",
    lifespan=lifespan,
)

@app.get(
    "/health",
    tags=["Service"],
    summary="Проверка работоспособности",
)
def health_check(settings: Settings = Depends(get_settings)):
    mode = "mock" if settings.use_mock or settings.openai_api_key == "your_api_key_here" else "live"
    return {"status": "ok", "mode": mode, "model": settings.openai_model}

@app.post(
    "/generate",
    response_model=ProductCardOutput,
    responses={
        400: {"model": ErrorResponse, "description": "Некорректный входной JSON"},
        502: {"model": ErrorResponse, "description": "Ошибка LLM API"},
    },
    tags=["Generation"],
    summary="Сгенерировать карточку товара",
)
def generate_product_card(
    product: ProductInput,
    settings: Settings = Depends(get_settings),
):
    """
    Принимает JSON с данными о товаре и возвращает структурированную карточку.
    Если данных недостаточно, поле `missing_data_warning` будет содержать список отсутствующих полей.
    """
    try:
        result = generate_card(product, settings)
        return result
    except APIError as e:
        logger.error(f"Ошибка LLM API: {e}")
        raise HTTPException(status_code=502, detail=f"Ошибка LLM API: {str(e)}")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервиса: {str(e)}")

@app.exception_handler(422)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "Некорректный входной JSON", "details": str(exc)},
    )
