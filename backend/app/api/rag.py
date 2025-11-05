from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
# Form暂时移除，因为python-multipart安装有问题
# from fastapi import Form
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.schemas import (
    KnowledgeBaseCreate, KnowledgeBaseResponse, RAGSearchRequest,
    RAGSearchResult, DocumentUploadRequest
)
from ..services.rag_service import RAGService, get_rag_service
from ..core.database import get_db
from ..core.config import settings
import os
import uuid
from fastapi.responses import FileResponse

router = APIRouter()

@router.post("/knowledge-bases", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    db: Session = Depends(get_db)
):
    """创建知识库"""
    try:
        rag_service = get_rag_service(db)
        return await rag_service.create_knowledge_base(kb_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-bases", response_model=List[KnowledgeBaseResponse])
async def get_knowledge_bases(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取知识库列表"""
    try:
        rag_service = get_rag_service(db)
        return rag_service.get_user_knowledge_bases(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 暂时注释掉File上传路由，因为FastAPI需要python-multipart来处理File参数
# @router.post("/knowledge-bases/{kb_id}/upload")
# async def upload_document_to_kb(
#     kb_id: int,
#     file: UploadFile = File(...),
#     chunk_size: int = Query(1000),
#     chunk_overlap: int = Query(200),
#     db: Session = Depends(get_db)
# ):
#     """上传文档到知识库"""
#     try:
#         # 验证文件类型
#         allowed_types = ['pdf', 'docx', 'txt', 'md', 'html']
#         file_extension = file.filename.split('.')[-1].lower()
#         if file_extension not in allowed_types:
#             raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")
# 
#         # 保存文件
#         upload_dir = os.path.join(settings.upload_dir, "documents")
#         os.makedirs(upload_dir, exist_ok=True)
# 
#         unique_filename = f"{uuid.uuid4()}.{file_extension}"
#         file_path = os.path.join(upload_dir, unique_filename)
# 
#         with open(file_path, 'wb') as buffer:
#             content = await file.read()
#             buffer.write(content)
# 
#         # 处理文档
#         upload_request = DocumentUploadRequest(
#             knowledge_base_id=kb_id,
#             file_path=file_path,
#             chunk_size=chunk_size,
#             chunk_overlap=chunk_overlap
#         )
# 
#         rag_service = get_rag_service(db)
#         result = await rag_service.upload_document(
#             upload_request, file_path, file.filename, file_extension
#         )
# 
#         return {
#             "message": "Document uploaded successfully",
#             "document_id": result["document_id"],
#             "filename": result["filename"],
#             "chunk_count": result["chunk_count"]
#         }
# 
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge-bases/search", response_model=List[RAGSearchResult])
async def search_knowledge_bases(
    search_request: RAGSearchRequest,
    db: Session = Depends(get_db)
):
    """搜索知识库"""
    try:
        rag_service = get_rag_service(db)
        return await rag_service.search_knowledge_base(search_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge-bases/generate-response")
async def generate_rag_response(
    search_request: RAGSearchRequest,
    model: str = Query("gpt-3.5-turbo"),
    db: Session = Depends(get_db)
):
    """生成RAG增强响应"""
    try:
        rag_service = get_rag_service(db)

        search_results = await rag_service.search_knowledge_base(search_request)

        # 生成响应
        response = await rag_service.generate_rag_response(
            search_request.query, search_results, model=model
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-bases/{kb_id}/stats")
async def get_knowledge_base_stats(
    kb_id: int,
    db: Session = Depends(get_db)
):
    """获取知识库统计信息"""
    try:
        rag_service = get_rag_service(db)
        stats = await rag_service.get_knowledge_base_stats(kb_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/knowledge-bases/documents/{doc_id}/reindex")
async def reindex_document(
    doc_id: int,
    db: Session = Depends(get_db)
):
    """重新索引文档"""
    try:
        rag_service = get_rag_service(db)
        await rag_service.update_document_index(doc_id)
        return {"message": "Document reindexed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/knowledge-bases/documents/{doc_id}")
async def delete_document(
    doc_id: int,
    db: Session = Depends(get_db)
):
    """删除文档"""
    try:
        rag_service = get_rag_service(db)
        await rag_service.delete_document(doc_id)
        return {"message": "Document deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))