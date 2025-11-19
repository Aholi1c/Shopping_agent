import os
import sys
import asyncio

# 确保可以导入 backend/app 下的代码
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.services.rag_service import get_rag_service
from app.models.schemas import KnowledgeBaseCreate, DocumentUploadRequest
from app.models.models import KnowledgeBase, Document, DocumentChunk


PHONE_KB_NAME = "手机导购知识库"
PHONE_KB_DESC = "手机导购专业知识（购买要点、预算分档、选型策略等）"


async def main():
    db = SessionLocal()
    try:
        rag_service = get_rag_service(db)

        # 查找或创建手机导购知识库
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.name == PHONE_KB_NAME).first()
        if kb:
            kb_id = kb.id
            print(f"已存在知识库: {PHONE_KB_NAME} (id={kb_id})，将清空旧文档后重新导入")
        else:
            kb_data = KnowledgeBaseCreate(
                name=PHONE_KB_NAME,
                description=PHONE_KB_DESC,
                user_id=None,
            )
            kb_resp = await rag_service.create_knowledge_base(kb_data)
            kb_id = kb_resp.id
            print(f"创建知识库: {PHONE_KB_NAME} (id={kb_id})")

        # 清空该知识库下的旧文档与分片
        old_docs = db.query(Document).filter(Document.knowledge_base_id == kb_id).all()
        if old_docs:
            doc_ids = [d.id for d in old_docs]
            db.query(DocumentChunk).filter(
                DocumentChunk.document_id.in_(doc_ids)
            ).delete(synchronize_session=False)
            db.query(Document).filter(Document.id.in_(doc_ids)).delete(
                synchronize_session=False
            )
            db.commit()
            print(f"已清空原有手机导购文档，共 {len(old_docs)} 个")

        # 准备要导入的文件路径
        file_path = os.path.join(BACKEND_DIR, "uploads", "documents", "phone_knowledge.md")
        file_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"未找到文件: {file_path}")

        # 上传并索引文档
        upload_req = DocumentUploadRequest(
            knowledge_base_id=kb_id,
            file_path=file_path,
            chunk_size=1000,
            chunk_overlap=200,
        )

        result = await rag_service.upload_document(
            upload_request=upload_req,
            file_path=file_path,
            original_name="phone_knowledge.md",
            file_type="md",
        )

        print("手机导购知识导入完成：")
        print(f"- 知识库 id: {kb_id}")
        print(f"- 文档 id: {result['document_id']}")
        print(f"- chunk 数量: {result['chunk_count']}")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())

