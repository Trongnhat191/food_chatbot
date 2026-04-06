# src/chat/engine.py
import os
import sys
from groq import Groq
from dotenv import load_dotenv
from embed.weaviate_client import WeaviateEmbeddingClient

# Đảm bảo load biến môi trường nếu chạy độc lập
load_dotenv()

def get_rag_recipe(query, preference=None):
    # Hướng C: Thêm sở thích vào query để cá nhân hóa
    if preference:
        query = f"{query} (Lưu ý đặc biệt: {preference})"

    # 1. Truy vấn ngữ cảnh từ Weaviate (Giống chat.py)
    with WeaviateEmbeddingClient() as client:
        # Lấy top 1 hoặc 2 tùy bạn, ở đây giữ top 1 cho gọn
        retrieve_context = client.retrieve_similar(
            os.getenv("WEAVIATE_COLLECTION", "RecipeDemo"), 
            query_text=query, 
            top_k=1
        )
        
    if not retrieve_context:
        return None

    # Format context để gửi cho LLM
    context_text = ""
    for obj in retrieve_context:
        context_text += (
            f"Tên món: {obj.properties.get('name')}\n"
            f"Nguyên liệu: {obj.properties.get('ingredients')}\n"
            f"Cách làm: {obj.properties.get('instructions')}\n\n"
        )

    # 2. Gọi Groq với đầy đủ tham số và System Prompt (Giống chat.py)
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # Kết hợp persona của chat.py và yêu cầu định dạng của Rasa
    system_prompt = (
        "Bạn là một trợ lý ảo giúp người dùng tìm kiếm công thức nấu ăn. "
        "Bạn sử dụng thông tin từ cơ sở dữ liệu để đưa ra gợi ý phù hợp nhất.\n"
        "BẮT BUỘC ĐỊNH DẠNG: Bạn phải chia cách làm thành các bước rõ ràng. "
        "Mỗi bước phải được ngăn cách CHÍNH XÁC bởi dấu gạch đứng '|'.\n"
        "Ví dụ: Bước 1: Sơ chế... | Bước 2: Ướp thịt... | Bước 3: Nấu..."
    )

    completion = client.chat.completions.create(
        model=os.getenv("MODEL_NAME"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Dữ liệu gốc:\n{context_text}\n\nCâu hỏi: {query}"}
        ],
        temperature=0.7, # Tăng một chút so với 0.5 để trả lời tự nhiên hơn
        max_completion_tokens=8192,
        top_p=1,
        # reasoning_effort="medium", # Lưu ý: Chỉ dùng nếu model hỗ trợ (như o1/DeepSeek-R1)
        stream=False # Rasa Action Server cần nhận toàn bộ text một lúc, không stream
    )
    
    return completion.choices[0].message.content

# Test thử độc lập giống chat.py
if __name__ == "__main__":
    test_query = "Cách nấu canh mồng tơi"
    print(f"--- Đang test engine với query: {test_query} ---")
    result = get_rag_recipe(test_query, preference="không ăn cay")
    print(result)