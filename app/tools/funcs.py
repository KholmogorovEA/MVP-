import os
import openai
from pydub import AudioSegment
import logging
from app.tools.decorator import VACAnalyzer 
from typing import List
from app.config import settings

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)  


ALLOWED_EXTENSIONS = {'wav', 'mp3'}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def convert_to_wav(file_path: str) -> str:
    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension == '.mp3':
        logger.debug(f"Конвертируем файл {file_path} в формат WAV")
        audio = AudioSegment.from_mp3(file_path)
        #audio = audio.set_frame_rate(16000)
        new_file_path = file_path.replace('.mp3', '.wav')
        audio.export(new_file_path, format='wav')
        logger.debug(f"Файл сконвертирован в {new_file_path}")
        return new_file_path
    logger.debug(f"Файл уже в формате WAV: {file_path}")
    return file_path


def stt_whisper_api(audio_file_path: str, prompt: str) -> str:
    logger.debug(f"Начинаем транскрипцию файла {audio_file_path} с использованием Whisper API")
    with open(audio_file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="ru",
            response_format='text',
            prompt="Евгений, всесоюзная нефтяная компания",
        )
    transcription_text = transcription
    #logger.debug(f"Транскрибированный текст: {transcription_text[:100]}...") 
    return transcription_text



@VACAnalyzer
def analyze_transcript(transcript_text: str, criteria: List[str], api_key: str) -> str:
    """
    Анализ транскрипции с помощью GPT-4. 
    transcript_text (str): Текст транскрипции для анализа.
    criteria (List[str]): Список критериев анализа.
    api_key (str): Ключ API для OpenAI.
    Returns:str: Результат анализа текста.
    """
  
    openai.api_key = api_key

    try:
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages = [
                        {
                            "role": "system",
                            "content": (
                                "Ты специалист по анализу расшифровок телефонных разговоров. "
                                "ВАЖНО: Выведи данные в формате 'Критерий: описание' и добавь конкретные примеры в описании."
                            )
                        },
                            {"role": "user", "content": f"Transcript: {transcript_text}. Проанализируйте текст по критериям:"},]
                            + [{"role": "user", "content": criterion} for criterion in criteria] + [
                            {"role": "assistant", "content": (
                                "Критерий: Задавал ли открытые вопросы\n"
                                "Описание: Да, менеджер задавал вопросы. Например: 'Как вы видите сотрудничество?' "
                                "или 'Что еще вас интересует?' Это подтверждает гибкий подход."
                            )}] # type: ignore
        )
      
        analysis_result = response.choices[0].message.content  # type: ignore
        logger.debug(f"Результат анализа: {analysis_result}") # type: ignore
        return analysis_result # type: ignore
    except Exception as e:
        logger.error(f"Ошибка при анализе транскрипции: {e}")
        raise e




# text = r"C:\Users\Evgenii\Desktop\NueroKK\app\uploads\Геннадий - Нет денег_transcript.txt"
def read_transcript(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"Файл '{file_path}' не найден.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")



def split_text(text, max_size=2600000):
    """Разделяет текст на части, чтобы не превышать лимит."""
    chunks = []
    while len(text) > max_size:
        split_point = text.rfind("\n", 0, max_size)
        if split_point == -1:
            split_point = max_size
        chunks.append(text[:split_point])
        text = text[split_point:]
    chunks.append(text)
    return chunks


import json
with open("radical.json", "r", encoding="utf-8") as f:
    json_radical = json.load(f)

with open("meta.json", "r", encoding="utf-8") as f:
    json_meta = json.load(f)

with open("handling_objections.json", "r", encoding="utf-8") as f:
    handling_objections = json.load(f)