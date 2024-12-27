import openai
import json
import logging
from typing import TypedDict, List, Dict
from app.config import settings
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)  



class Objection(TypedDict):
    P: str
    M: str
    H: str
    S: str

HandlingObjections = Dict[str, Objection]



def get_job_with_objections(transcript_text: str, client, handling_objections: HandlingObjections) -> str:
    """
    Анализирует возражения и предоставялет пример работы над ними.
    - transcript_text (str): Текст записи звонка (диалог менеджера и клиента).
    - handling_objections (TypedDict): Данные работы с возражениями.
    - client: openai
    - Return str: Пример работы с возражениями.
    """
  
    system = f"""
                Проанализируй возражения клиента. 
                Вот примеры работы с возражениями:
                {json.dumps(handling_objections, ensure_ascii=False, indent=2)}

                Разговор:
                {transcript_text}

                Определи:
                1. Возражение.
                2. Отработай возражения исходя из примеров.
               

                Вывод данных обеспечь в виде: (Возражение Клиента: Работа с этим возражением по системе PMHS) 
            """


    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": """Сделай работу по отработке возражений, твоя задача убедить клиента. 
             Также очисти информацию от звездочек ** и ### хэш тэгов."""},
           
        ]
    )

   
    result = response.choices[0].message.content
    result_cleaned = result.replace('**', '').strip()
    logger.debug(f"Результат psy analize: {result_cleaned}")
    return result_cleaned
