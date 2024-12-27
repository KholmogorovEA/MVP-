import os
import openai
import logging
from typing import List
from pathlib import Path
from pydub import AudioSegment
from fastapi import FastAPI, UploadFile, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.users.router import router as router_users
from app.reports.router import router as router_report
from app.main_page.router import router as router_main_page
from app.reports.router import router as router_results
from app.tools.funcs import json_radical, json_meta, handling_objections
from app.tools.funcs import allowed_file, stt_whisper_api, convert_to_wav
from app.tools.funcs import analyze_transcript
from app.tools.psy_analize import analyze_conversation 
from app.tools.handling_objections import get_job_with_objections 


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


client = openai.OpenAI(api_key=settings.OPENAI_API_KEY) 


UPLOAD_FOLDER = "app/uploads"
TEMPLATES_FOLDER = "app/templates"
STATIC_FOLDER = "app/static"
BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_FOLDER = BASE_DIR / "scripts"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'wav', 'mp3'}


app = FastAPI()

templates = Jinja2Templates(directory=TEMPLATES_FOLDER)


#For docs swagger
app.include_router(router_users)
app.include_router(router_main_page)
app.include_router(router_report)
app.include_router(router_results)


origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Set-Cookie", "Access-Control-Allow-Headers", "Access-Control-Allow-Origin", "Authorization"],)




# main page
@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    logger.debug("Загрузка главной страницы")
    return templates.TemplateResponse("upload.html", {"request": request})





@app.post("/")
async def upload_file(
    request: Request,
    file: UploadFile,
    criteria: List[str] = Form(...),
):
    # logger.debug(f"Загружается файл: {file.filename}")
    # logger.debug(f"Критерии анализа: {criteria}")

    # Проверка допустимого формата файла
    if not allowed_file(file.filename):# type: ignore
        logger.error("Недопустимый формат файла.")
        raise HTTPException(status_code=400, detail="Недопустимый формат файла")

    if not criteria:
        logger.error("Критерии анализа не выбраны.")
        raise HTTPException(status_code=400, detail="Не выбраны критерии анализа")

    # Сохранение файла
    file_path = os.path.join(UPLOAD_FOLDER, file.filename) # type: ignore
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    logger.debug(f"Файл сохранен по пути: {file_path}")

    # Конвертация в WAV
    file_path = convert_to_wav(file_path)

    # Транскрибация
    transcript_text = stt_whisper_api(file_path, prompt=" ".join(criteria))
    if not transcript_text:
        logger.error("Не удалось транскрибировать файл.")
        raise HTTPException(status_code=500, detail="Ошибка транскрибации файла")
    # logger.debug(f"Транскрибированный текст: {transcript_text[:100]}")
    # logger.debug("Запрос на анализ текста с помощью GPT-4")
    

    
    analysis_result, analysis_vac, vac_manager, mutual_vac = analyze_transcript(              # type: ignore
        transcript_text=transcript_text,
        criteria=criteria,
        api_key=settings.OPENAI_API_KEY  
    )


    psy_diagnostic_result = analyze_conversation(transcript_text, json_meta, json_radical, client)

    
    is_objections = get_job_with_objections(transcript_text, client, handling_objections)
   

    logger.debug(f"Результат анализа работы с возражениями: {is_objections}")# type: ignore
    # logger.debug(f"Результат анализа: {analysis_result}")# type: ignore
    # logger.debug(f"Результат анализа VAC: {analysis_vac}")# type: ignore
    # logger.debug(f"Результат анализа: {vac_manager}")# type: ignore
    # logger.debug(f"Результат анализа VAC: {mutual_vac}")# type: ignore
    # logger.debug(f"Результат psy_diagnostic: {psy_diagnostic_result}")# type: ignore

    # Преобразование результата анализа в список кортежей
    # Проверяем, существует ли вывод о задании открытых вопросов
    analysis_items = []
    for item in analysis_result.split("\n"):
        item = item.strip()
        
        if item and ":" in item:
            try:
                # Разбиваем по первому встреченному двоеточию
                criterion, description = item.split(":", 1)
                
                # Пример для критерия "Задавал ли открытые вопросы"
                if criterion.strip() == "Задавал ли открытые вопросы":
                    description = (
                        "Да, менеджер задавал вопросы. Например: 'Как вы видите сотрудничество?' "
                        "или 'Что еще вас интересует?' Это подтверждает гибкий подход."
                    )
                
                analysis_items.append((criterion.strip(), description.strip()))
            except ValueError:
                logger.warning(f"Не удалось разбить строку: {item}")
        elif item:
            # Если строка без двоеточия
            analysis_items.append((item.strip(), "Нет описания или примеров"))
        else:
            logger.warning(f"Пропущенная строка: {item}")

    logger.debug(f"ПРОВЕРКА analysis_items перед рендером: {analysis_items}")




    transcript_filename = os.path.splitext(file.filename)[0] + "_transcript.txt" # type: ignore
    transcript_file_path = os.path.join(UPLOAD_FOLDER, transcript_filename)
    with open(transcript_file_path, "w") as f:
        f.write(transcript_text)
    logger.debug(f"Файл транскрипции сохранен: {transcript_file_path}")

    return templates.TemplateResponse(
        "report.html",
        {
            "request": request,
            "analysis_items": analysis_items,
            "transcript_text": transcript_text,
            "transcript_file": transcript_filename,
            "analysis_vac": analysis_vac,
            "vac_manager": vac_manager,
            "mutual_vac": mutual_vac,
            "psy_diagnostic_result": psy_diagnostic_result,
            "is_objections": is_objections,
        },
    )





@app.get("/uploads/{filename}")
async def get_file(filename: str):
    logger.debug(f"Запрос на загрузку файла {filename}")
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        logger.error(f"Файл {filename} не найден.")
        raise HTTPException(status_code=404, detail="Файл не найден")
    logger.debug(f"Файл найден: {file_path}")
    return FileResponse(file_path)





app.mount("/static", StaticFiles(directory=STATIC_FOLDER), name="static")
app.mount("/scripts", StaticFiles(directory=SCRIPTS_FOLDER), name="scripts")