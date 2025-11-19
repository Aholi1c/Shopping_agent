import asyncio
import os, sys

# Ensure backend/app is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.services.ecommerce_rag_service import EcommerceRAGService
from app.services.conversation_service import ConversationService
from app.models.schemas import ProductRecommendationRequest, ChatRequest
from app.services.shopping_service import ShoppingService
from app.core.config import settings

# Simple mock for LLM chat_completion
async def mock_chat_completion(self, messages, model=None, max_tokens=None, temperature=None, stream=False):
    sys_msg = ''
    if messages and messages[0]['role'] == 'system':
        sys_msg = messages[0]['content']
    return {
        'content': '[MOCK RESPONSE] 综合推荐: 已整合知识与商品。\nSYSTEM_PROMPT_HEAD:\n' + sys_msg[:300],
        'model_used': model or 'mock-model',
        'tokens_used': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
    }

# Optional mock products if Onebound not configured
MOCK_PRODUCTS = [
    {
        'title': '示例手机 A 8GB+256GB 1亿像素', 'price': 2899, 'original_price': 3299,
        'discount_rate': 0.12, 'rating': 4.7, 'review_count': 12000, 'sales_count': 50000,
        'product_url': 'https://example.com/a'
    },
    {
        'title': '示例手机 B 12GB+512GB 旗舰影像', 'price': 3099, 'original_price': 3699,
        'discount_rate': 0.16, 'rating': 4.8, 'review_count': 22000, 'sales_count': 65000,
        'product_url': 'https://example.com/b'
    },
    {
        'title': '示例手机 C 8GB+256GB 长续航', 'price': 2599, 'original_price': 2999,
        'discount_rate': 0.13, 'rating': 4.6, 'review_count': 8000, 'sales_count': 42000,
        'product_url': 'https://example.com/c'
    }
]

async def maybe_patch_shopping(service: ShoppingService):
    if not settings.onebound_api_key or settings.onebound_api_key == 'test_api_key':
        async def mock_search_products(request, user_id=None):
            return {'products': MOCK_PRODUCTS, 'total_count': len(MOCK_PRODUCTS)}
        service.search_products = mock_search_products

async def run_recommendation_flow(session):
    service = EcommerceRAGService(session)
    if service.llm_service:
        service.llm_service.chat_completion = mock_chat_completion.__get__(service.llm_service, type(service.llm_service))
    # Patch shopping if needed
    await maybe_patch_shopping(service.shopping_service)
    req = ProductRecommendationRequest(query='预算3000拍照好的手机', budget=3000, preferences={'camera': '优先'}, limit=5)
    result = await service.recommend_with_taobao(req)
    print('[TEST] /ecommerce/recommendations keys:', list(result.keys()))
    print('[TEST] knowledge_snippets count:', len(result.get('knowledge_snippets', [])))
    print('[TEST] products count:', len(result.get('products', [])))
    print('[TEST] recommendation_text snippet:', (result.get('recommendation_text') or '')[:180])

async def run_chat_flow(session):
    conv_service = ConversationService(session)
    conv_service.llm_service.chat_completion = mock_chat_completion.__get__(conv_service.llm_service, type(conv_service.llm_service))
    chat_req = ChatRequest(message='帮我选手机，预算3000，拍照要好', use_memory=False)
    resp = await conv_service.process_chat_message(chat_req)
    print('[TEST] /chat response model_used:', resp.model_used)
    print('[TEST] assistant message snippet:', resp.response[:180])

async def main():
    session = SessionLocal()
    try:
        await run_recommendation_flow(session)
        await run_chat_flow(session)
    finally:
        session.close()

if __name__ == '__main__':
    asyncio.run(main())
