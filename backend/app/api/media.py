from fastapi import APIRouter, HTTPException, UploadFile, File
# Form暂时移除，因为python-multipart安装有问题
# from fastapi import Form
from typing import Optional
from ..services.media_service import media_service
from ..models.schemas import TranscriptionRequest, TranscriptionResponse, SpeechRequest, SpeechResponse, ImageAnalysisRequest, ImageAnalysisResponse
from ..services.llm_service import get_llm_service
from fastapi.responses import FileResponse
import os
from datetime import datetime

router = APIRouter()

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    request: TranscriptionRequest
):
    """
    转录音频文件
    """
    try:
        llm_service = get_llm_service()
        result = await llm_service.transcribe_audio(request.audio_url, request.language)
        return TranscriptionResponse(
            text=result["text"],
            language=result["language"],
            confidence=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 暂时注释掉File上传路由，因为FastAPI需要python-multipart来处理File参数
# @router.post("/transcribe/upload")
# async def transcribe_uploaded_audio(
#     file: UploadFile = File(...),
#     language: Optional[str] = None
# ):
#     """
#     转录上传的音频文件
#     """
#     try:
#         # 保存文件
#         file_path = await media_service.save_upload_file(file, "audio")
# 
#         # 转录音频
#         result = await media_service.transcribe_audio(file_path, language)
# 
#         return TranscriptionResponse(
#             text=result["text"],
#             language=result["language"],
#             confidence=result.get("confidence")
#         )
# 
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/speech", response_model=SpeechResponse)
async def text_to_speech(
    request: SpeechRequest
):
    """
    文本转语音
    """
    try:
        llm_service = get_llm_service()
        audio_file_path = await llm_service.text_to_speech(request.text, request.voice)

        return SpeechResponse(
            audio_url=audio_file_path,
            duration=None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 暂时注释掉语音上传路由，因为可能需要File参数
# @router.post("/speech/upload")
# async def text_to_speech_upload(
#     request: SpeechRequest
# ):
#     """
#     文本转语音并上传
#     """
#     try:
#         audio_file_path = await media_service.text_to_speech(request.text, request.voice)
# 
#         return SpeechResponse(
#             audio_url=audio_file_path,
#             duration=None
#         )
# 
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_image(
    request: ImageAnalysisRequest
):
    """
    分析图像
    """
    try:
        llm_service = get_llm_service()
        result = await llm_service.analyze_image(request.image_url, request.prompt)

        return ImageAnalysisResponse(
            analysis=result["analysis"],
            description=result["analysis"],
            tags=None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 暂时注释掉File上传路由，因为FastAPI需要python-multipart来处理File参数
# @router.post("/analyze-image/upload")
# async def analyze_uploaded_image(
#     file: UploadFile = File(...),
#     request: Optional[ImageAnalysisRequest] = None
# ):
#     """
#     分析上传的图像
#     """
#     try:
#         # 验证文件类型
#         if not file.content_type or not file.content_type.startswith("image/"):
#             raise HTTPException(status_code=400, detail="File must be an image")
# 
#         # 保存并处理图像
#         file_path = await media_service.save_upload_file(file, "images")
#         processed_path, image_info = await media_service.process_image(file_path)
# 
#         # 分析图像
#         prompt = request.prompt if request else "Describe this image in detail."
#         result = await llm_service.analyze_image(processed_path, prompt)
# 
#         return ImageAnalysisResponse(
#             analysis=result["analysis"],
#             description=result["analysis"],
#             tags=None
#         )
# 
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """
    获取音频文件
    """
    file_path = os.path.join(settings.upload_dir, "audio", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(file_path)

@router.get("/images/{filename}")
async def get_image_file(filename: str):
    """
    获取图像文件
    """
    file_path = os.path.join(settings.upload_dir, "images", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(file_path)