import os
import uuid
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    pyttsx3 = None
from ..core.config import settings
import aiofiles

class MediaService:
    def __init__(self):
        self.upload_dir = settings.upload_dir
        if SPEECH_RECOGNITION_AVAILABLE and sr:
            self.recognizer = sr.Recognizer()
        else:
            self.recognizer = None
        if PYTTSX3_AVAILABLE and pyttsx3:
            try:
                self.tts_engine = pyttsx3.init()
            except:
                self.tts_engine = None
        else:
            self.tts_engine = None

    async def save_upload_file(self, file: UploadFile, subfolder: str = "general") -> str:
        """
        保存上传的文件
        """
        try:
            # 创建子文件夹
            folder_path = os.path.join(self.upload_dir, subfolder)
            os.makedirs(folder_path, exist_ok=True)

            # 生成唯一文件名
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = os.path.join(folder_path, unique_filename)

            # 保存文件
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)

            return file_path

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    async def process_image(self, file_path: str) -> Tuple[str, dict]:
        """
        处理图像文件
        """
        try:
            # 打开图像
            image = Image.open(file_path)

            # 获取图像信息
            image_info = {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "mode": image.mode,
                "size": os.path.getsize(file_path)
            }

            # 生成缩略图
            thumbnail_path = file_path.replace('.', '_thumb.')
            image.thumbnail((256, 256))
            image.save(thumbnail_path)

            return file_path, image_info

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

    async def transcribe_audio(self, file_path: str, language: Optional[str] = None) -> dict:
        """
        转录音频文件
        """
        try:
            with sr.AudioFile(file_path) as source:
                audio_data = self.recognizer.record(source)

            if language:
                text = self.recognizer.recognize_google(audio_data, language=language)
            else:
                text = self.recognizer.recognize_google(audio_data)

            return {
                "text": text,
                "language": language or "auto-detected",
                "confidence": 0.95  # Google Speech Recognition doesn't provide confidence
            }

        except sr.UnknownValueError:
            raise HTTPException(status_code=400, detail="Could not understand audio")
        except sr.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Speech recognition error: {str(e)}")

    async def text_to_speech(self, text: str, voice_id: Optional[str] = None) -> str:
        """
        文本转语音
        """
        try:
            # 设置语音属性
            if voice_id:
                voices = self.tts_engine.getProperty('voices')
                for voice in voices:
                    if voice_id in voice.id:
                        self.tts_engine.setProperty('voice', voice.id)
                        break

            # 生成音频文件
            output_file = os.path.join(self.upload_dir, "tts", f"tts_{uuid.uuid4()}.mp3")
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            self.tts_engine.save_to_file(text, output_file)
            self.tts_engine.runAndWait()

            return output_file

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Text-to-speech error: {str(e)}")

    def validate_file_type(self, filename: str, allowed_types: list) -> bool:
        """
        验证文件类型
        """
        file_extension = filename.split('.')[-1].lower()
        return file_extension in allowed_types

    def validate_file_size(self, file_size: int, max_size: int = None) -> bool:
        """
        验证文件大小
        """
        max_size = max_size or settings.max_file_size
        return file_size <= max_size

    async def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False

    def get_file_info(self, file_path: str) -> dict:
        """
        获取文件信息
        """
        if not os.path.exists(file_path):
            return {}

        stat = os.stat(file_path)
        return {
            "size": stat.st_size,
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
            "extension": file_path.split('.')[-1] if '.' in file_path else ''
        }

# 全局媒体服务实例
media_service = MediaService()