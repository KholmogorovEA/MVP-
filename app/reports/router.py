from fastapi import Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse 
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
from typing import List
from fastapi import APIRouter, Request, Depends

# Инициализация логирования
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Папки для загрузок и шаблонов

TEMPLATES_FOLDER = "app/templates"


templates = Jinja2Templates(directory=TEMPLATES_FOLDER)

router = APIRouter(
    prefix="/report",
    tags=["Отчет по анализу звонков"]
)


@router.post("", response_class=HTMLResponse)
async def report_page(
    request: Request,
    analysis_result: str = Form(...),
    transcript_text: str = Form(...),
    transcript_file: str = Form(...),
):
    logger.debug(f"Получены параметры: analysis_result={analysis_result}, transcript_text={transcript_text}, transcript_file={transcript_file}")

    if not analysis_result or not transcript_text or not transcript_file:
        raise HTTPException(status_code=400, detail="Не все данные были переданы.")

    # Подготовка данных для таблицы
    analysis_items = []
    for item in analysis_result.split("\n"):
        if ":" in item:
            criterion, description = item.split(":", 1)
            analysis_items.append((criterion.strip(), description.strip()))

    logger.debug(f"Подготовленные данные для отчета: {analysis_items}")

    # Рендеринг шаблона
    return templates.TemplateResponse(
        "report.html",
        {
            "request": request,
            "analysis_items": analysis_items,
            "transcript_text": transcript_text,
            "transcript_file": transcript_file
        },
    )