from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
from ..services.llm_service import get_llm_service
from ..services.conversation_service import ConversationService
from ..core.database import SessionLocal
from ..models.schemas import WebSocketMessage

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """
        建立WebSocket连接
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        """
        断开WebSocket连接
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, client_id: str):
        """
        发送个人消息
        """
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except:
                self.disconnect(client_id)

    async def broadcast(self, message: dict):
        """
        广播消息给所有连接
        """
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_text(json.dumps(message))
            except:
                self.disconnect(client_id)

    async def is_connected(self, client_id: str) -> bool:
        """
        检查客户端是否连接
        """
        return client_id in self.active_connections

# 全局连接管理器
manager = ConnectionManager()

async def handle_websocket_chat(websocket: WebSocket, client_id: str):
    """
    处理WebSocket聊天
    """
    await manager.connect(websocket, client_id)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message_data = json.loads(data)

            message_type = message_data.get("type")
            payload = message_data.get("data", {})

            if message_type == "chat":
                await handle_chat_message(websocket, client_id, payload)
            elif message_type == "ping":
                await manager.send_personal_message({"type": "pong"}, client_id)
            elif message_type == "transcribe":
                await handle_audio_transcription(websocket, client_id, payload)
            elif message_type == "analyze_image":
                await handle_image_analysis(websocket, client_id, payload)

    except WebSocketDisconnect:
        manager.disconnect(client_id)

async def handle_chat_message(websocket: WebSocket, client_id: str, payload: dict):
    """
    处理聊天消息
    """
    try:
        message = payload.get("message", "")
        conversation_id = payload.get("conversation_id")
        model = payload.get("model", "gpt-3.5-turbo")

        # 发送处理中消息
        await manager.send_personal_message({
            "type": "processing",
            "data": {"message": "正在处理您的消息..."}
        }, client_id)

        # 获取数据库会话
        db = SessionLocal()
        conversation_service = ConversationService(db)

        try:
            # 构建消息历史
            messages = []
            if conversation_id:
                messages = conversation_service.get_conversation_messages(conversation_id)
                message_history = [{"role": msg.role, "content": msg.content} for msg in messages]
            else:
                message_history = [{"role": "user", "content": message}]

            # 发送流式响应
            await manager.send_personal_message({
                "type": "chat_start",
                "data": {"conversation_id": conversation_id}
            }, client_id)

            # 获取LLM响应
            llm_service = get_llm_service()
            llm_response = await llm_service.chat_completion(
                messages=message_history,
                model=model,
                stream=True
            )

            response_content = ""
            for chunk in llm_response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    response_content += content

                    await manager.send_personal_message({
                        "type": "chat_chunk",
                        "data": {"content": content}
                    }, client_id)

                    # 添加小延迟以显示流式效果
                    await asyncio.sleep(0.01)

            # 发送完成消息
            await manager.send_personal_message({
                "type": "chat_complete",
                "data": {
                    "response": response_content,
                    "conversation_id": conversation_id
                }
            }, client_id)

        finally:
            db.close()

    except Exception as e:
        await manager.send_personal_message({
            "type": "error",
            "data": {"message": f"处理消息时出错: {str(e)}"}
        }, client_id)

async def handle_audio_transcription(websocket: WebSocket, client_id: str, payload: dict):
    """
    处理音频转录
    """
    try:
        audio_url = payload.get("audio_url", "")
        language = payload.get("language")

        await manager.send_personal_message({
            "type": "transcription_start",
            "data": {"message": "正在转录音频..."}
        }, client_id)

        llm_service = get_llm_service()
        result = await llm_service.transcribe_audio(audio_url, language)

        await manager.send_personal_message({
            "type": "transcription_complete",
            "data": {
                "text": result["text"],
                "language": result["language"]
            }
        }, client_id)

    except Exception as e:
        await manager.send_personal_message({
            "type": "error",
            "data": {"message": f"音频转录失败: {str(e)}"}
        }, client_id)

async def handle_image_analysis(websocket: WebSocket, client_id: str, payload: dict):
    """
    处理图像分析
    """
    try:
        image_url = payload.get("image_url", "")
        prompt = payload.get("prompt", "Describe this image in detail.")

        await manager.send_personal_message({
            "type": "analysis_start",
            "data": {"message": "正在分析图像..."}
        }, client_id)

        llm_service = get_llm_service()
        result = await llm_service.analyze_image(image_url, prompt)

        await manager.send_personal_message({
            "type": "analysis_complete",
            "data": {
                "analysis": result["analysis"],
                "model_used": result["model_used"]
            }
        }, client_id)

    except Exception as e:
        await manager.send_personal_message({
            "type": "error",
            "data": {"message": f"图像分析失败: {str(e)}"}
        }, client_id)