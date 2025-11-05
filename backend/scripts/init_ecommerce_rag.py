#!/usr/bin/env python3
"""
初始化电商RAG知识库脚本
"""

import sys
import os

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# 设置环境变量
os.environ['PYTHONPATH'] = backend_dir

# 导入服务
from services.ecommerce_rag_service import EcommerceRAGService
from app.core.database import SessionLocal

def main():
    print("开始初始化电商RAG知识库...")

    # 创建数据库会话
    db = SessionLocal()

    try:
        # 创建RAG服务
        rag_service = EcommerceRAGService(db)

        # 构建知识库
        vector_store = rag_service.build_knowledge_base(
            data_dir="../data/ecommerce",
            rebuild=True
        )

        print("知识库初始化完成！")

    except Exception as e:
        print(f"初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()