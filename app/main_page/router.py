import os
import openai
from pydub import AudioSegment
from fastapi import FastAPI, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter, Request, Depends
from app.tools.funcs import allowed_file, stt_whisper_api, convert_to_wav
from app.config import settings

# Инициализация логирования
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Инициализация OpenAI API клиента
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)  # Замените на ваш API ключ

# Папки для загрузок и шаблонов

TEMPLATES_FOLDER = "app/templates"

templates = Jinja2Templates(directory=TEMPLATES_FOLDER)

router = APIRouter(
    prefix="/Главная",
    tags=["Главная страница"]
)


# Главная страница
@router.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    logger.debug("Загрузка главной страницы")
    return templates.TemplateResponse("upload.html", {"request": request})




