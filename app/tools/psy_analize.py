import openai
import json
import logging
from app.config import settings
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)  



def analyze_conversation(transcript: str, json_radical, json_meta, client) -> str:
    """
    Анализирует текст разговора по радикалам и метапрограммам.
    - transcript (str): Текст записи звонка (диалог менеджера и клиента).
    - json_data (dict): Данные с радикалами и метапрограммами в формате JSON.
    - openai_api_key (str): Ключ API для OpenAI.
    - str: Результат анализа разговора.
    """
  
    system = f"""
                Проанализируй текст разговора и определи, какие радикалы и метапрограммы выражены у клиента и менеджера. 
                Вот описание радикалов и метапрограмм:
                {json.dumps(json_radical, ensure_ascii=False, indent=2)}, {json.dumps(json_meta, ensure_ascii=False, indent=2)}

                Разговор:
                {transcript}

                Определи:
                1. Какие метапрограммы проявляет клиент.
                2. Какие метапрограммы проявляет менеджер.
                3. Какой радикал у клиента.
                4. Какой радикал у менеджера.

                Вывод данных обеспечь в виде: (Метапрограмма менеджера: Описание) Задача твоя: предоставить отчет отдельно по Клиенту и отдельно по Менеджеру.  
            """


    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": """Проведи анализ и предоставь подробную информацию для таблицы! 
             Также очисти информацию от звездочек и ### хэш тэгов. Задача твоя: предоставить отчет отдельно по Клиенту и отдельно по Менеджеру"""},
           
        ]
    )

   
    psy_result = response.choices[0].message.content
    psy_result_cleaned = psy_result.replace('**', '').strip()
    psy_result_cleaned = psy_result.replace("Отчет по Клиенту", "\n\nОтчет по Клиенту: ")
    psy_result_cleaned = psy_result.replace("Отчет по Менеджеру", "\n\nОтчет по Менеджеру: ")
    logger.debug(f"Результат psy analize: {psy_result_cleaned}")
    return psy_result_cleaned
