import os
import openai
from pydub import AudioSegment
import logging
from typing import List, Callable
import functools  # узнать !!!
import re
from app.config import settings

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)  


# text = r"C:\Users\Evgenii\Desktop\NueroKK\app\uploads\Геннадий - Нет денег_transcript.txt"



def split_channels(client, transcript, *args, **kwargs):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
            {"role": "system", "content": "Ты помогаешь разбить диалог на Клиента и Менеджера."},
            {"role": "user", "content": f"Разбей диалог:\n\n{transcript}\n\nНа роли Клиента и Менеджера. Вывод спикеров Менеджер: и Клиент: запиши без звездочек"}
        ]
        )
        
        result = response.choices[0].message.content  # type: ignore
        logger.debug(f"Результат анализа: {result}") # type: ignore
        

        client_replicas = re.findall(r'Клиент: (.+)', result)
        client_text = "\n".join(client_replicas)

        manager_replicas = re.findall(r'Менеджер: (.+)', result)
        manager_text = "\n".join(manager_replicas)
        

        return result, client_text, manager_text
    except Exception as e:
        logger.error(f"Ошибка при анализе транскрипции: {e}")
        raise e.add_note(f"Ошибка когото характера не понятного") # type: ignore



# Декоратор для вызова функции извлечения речи клиента
def extract_client_decorator(func):
    @functools.wraps(func)
    def wrapper(cls, text: str, api_key: str, *args, **kwargs):
        result, channel_client, channel_manager = split_channels(client, text, api_key)
        # Вызов оригинальной функции с речью клиента и манагера classmethod @extract_client_decorator
        return func(cls, channel_client, channel_manager, api_key, *args, **kwargs)
    return wrapper


class VACAnalyzer:
    """
    Класс для анализа VAC (Visual, Acoustic, Kinesthetic) текста.
    """
    VAC_WORDS = {
        "VISUAL": [
            "увидел", "заметил", "образ", "яркий", "цвет", "видение", "картинка",
            "осмотрел", "наблюдал", "светлый", "разглядывать", "фокус", "перспектива", "зрение"
        ],
        "AUDIAL": [
            "услышал", "звонко", "звенит", "громко", "шумно", "тише", "разговоры",
            "поговорить", "послышалось", "гармония", "эхо", "акустика", "шепот", "напев"
        ],
        "KINESTETIC": [
            "ощущение", "тёплый", "холодный", "прикосновение", "тяжесть", "лёгкость",
            "подтолкнул", "тронул", "двигаться", "прыгать", "касание", "напряжение", "расслабление"
        ]
    }

    def __init__(self, func: Callable):
        self.func = func

    def __call__(self, *args, **kwargs):
        # Вызов оригинальной функции
        result = self.func(*args, **kwargs)
        # Анализ VAC
        transcript_text = kwargs.get("transcript_text") or args[0]
        api_key = kwargs.get("api_key") or args[-1]
        vac_result, vac_manager, mutual_vac = self.analyze_vac(transcript_text, api_key) # type: ignore
        logger.debug(f"Результат анализа VAC: {vac_result[:100]}")
        return result, vac_result, vac_manager, mutual_vac


    @classmethod
    @extract_client_decorator
    def analyze_vac(cls, channel_client: str, channel_manager: str, api_key: str) -> str:
        """
        Анализ VAC текста с помощью GPT-4.
        """
        
        openai.api_key = api_key

        try:
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": """
                        Вы эксперт в определении предпочтений восприятия информации Клиентов в тексте диалога Менеджер - Клиент. Задача максимально точно определить тип Клиента (VAC): визуал (VISUAL), аудиал (AUDIAL), кинестетик (KINESTETIC). 
                        На основе слов Клиента, определи доминирующий стиль восприятия по словам, характерным для каждой группы:
                        1. VISUAL: слова и выражения, связанные с видением, зрением, образами, светом, цветами.
                        2. AUDIAL: слова и выражения, связанные со звуком, слухом, мелодиями, громкостью.
                        3. KINESTETIC: слова и выражения, связанные с физическими ощущениями, движением, теплом, холодом, прикосновениями.
                        ОбЯЗАТЕЛЬНО объясни твой выбор, ссылаясь на конкретные слова из текста."""},

                    {"role": "user", "content": f"Transcript: {channel_client}. Проанализируйте текст, опираясь на группы слов {cls.VAC_WORDS}"}
                ]
            )
            
            vac_result = response.choices[0].message.content


            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": """
                        Вы эксперт в определении предпочтений восприятия информации Клиентов в тексте диалога Менеджер - Клиент. Задача максимально точно определить тип Менеджера (VAC): визуал (VISUAL), аудиал (AUDIAL), кинестетик (KINESTETIC). 
                        На основе слов Менеджера, определи доминирующий стиль восприятия по словам, характерным для каждой группы:
                        1. VISUAL: слова и выражения, связанные с видением, зрением, образами, светом, цветами.
                        2. AUDIAL: слова и выражения, связанные со звуком, слухом, мелодиями, громкостью.
                        3. KINESTETIC: слова и выражения, связанные с физическими ощущениями, движением, теплом, холодом, прикосновениями.
                        ОбЯЗАТЕЛЬНО объясни твой выбор, ссылаясь на конкретные слова из текста."""},

                    {"role": "user", "content": f"Transcript: {channel_manager}. Проанализируйте текст, опираясь на группы слов {cls.VAC_WORDS}"}
                ]
            )
            
            vac_manager = response.choices[0].message.content  

            # определяем совпадения
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": """
                        Вы эксперт в определении (VAC) предпочтений восприятия информации по тексту диалога Менеджер - Клиент.
                        Задача максимально точно определить совпадения по (VAC): визуал (VISUAL), аудиал (AUDIAL), кинестетик (KINESTETIC) между Менеджером и Клиентом. 
                        На основе слов Менеджера и Клиента, определи общие стили восприятия по их словам, характерным для каждой группы:
                        1. VISUAL: слова и выражения, связанные с видением, зрением, образами, светом, цветами.
                        2. AUDIAL: слова и выражения, связанные со звуком, слухом, мелодиями, громкостью.
                        3. KINESTETIC: слова и выражения, связанные с физическими ощущениями, движением, теплом, холодом, прикосновениями.
                        ОбЯЗАТЕЛЬНО объясни твой выбор, ссылаясь на конкретные слова из текста."""},

                    {"role": "user", "content": f"Слова Менеджера: {channel_manager}, Слова Клиента: {channel_client}. Проанализируйте слова и найди общее между Мнеджером и Клиентом, опираясь на группы слов {cls.VAC_WORDS}"}
                ]
            )
            
            mutual_vac = response.choices[0].message.content  

            logger.debug(f"Результат анализа VAC клиента: {vac_result}")
            logger.debug(f"Результат анализа VAC менеджера: {vac_manager}")
            logger.debug(f"Результат анализа VAC Схожести: {mutual_vac}")
            
            return vac_result, vac_manager, mutual_vac # type: ignore
        except Exception as e:
            logger.error(f"Ошибка при анализе транскрипции: {e}")
            raise e
        

        