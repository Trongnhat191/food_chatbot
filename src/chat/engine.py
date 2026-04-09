# src/chat/engine.py
import os
import sys
from groq import Groq
from dotenv import load_dotenv
from embed.weaviate_client import WeaviateEmbeddingClient

load_dotenv()

def get_rag_recipe(query, preference=None):
    if preference:
        query = f"{query} (Lưu ý đặc biệt: {preference})"

    # 1. Truy vấn ngữ cảnh từ Weaviate
    with WeaviateEmbeddingClient() as client:
        retrieve_context = client.retrieve_similar(
            os.getenv("WEAVIATE_COLLECTION", "RecipeDemo"), 
            query_text=query, 
            top_k=1 # Giữ nguyên top 1 để tiết kiệm token
        )
        
    if not retrieve_context:
        return None

    # --- BƯỚC SỬA ĐỔI QUAN TRỌNG: GIỚI HẠN DỮ LIỆU ĐẦU VÀO ---
    context_text = ""
    for obj in retrieve_context:
        # Lấy dữ liệu và cắt bớt nếu nó quá dài (giới hạn mỗi phần khoảng 2000 ký tự)
        name = obj.properties.get('name', '')[:200]
        ingredients = obj.properties.get('ingredients', '')[:1500]
        instructions = obj.properties.get('instructions', '')[:2000]
        
        context_text += (
            f"Tên món: {name}\n"
            f"Nguyên liệu: {ingredients}\n"
            f"Cách làm: {instructions}\n\n"
        )

    # 2. Gọi Groq với System Prompt tối ưu
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    system_prompt = (
        "Bạn là trợ lý nấu ăn. Dựa vào dữ liệu gốc để trả lời câu hỏi.\n"
        "QUY ĐỊNH: Chia cách làm thành các bước rõ ràng. "
        "Ngăn cách các bước bằng dấu gạch đứng '|'. Ví dụ: Bước 1... | Bước 2..."
    )

    try:
        completion = client.chat.completions.create(
            model=os.getenv("MODEL_NAME"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Dữ liệu gốc:\n{context_text}\n\nCâu hỏi: {query}"}
            ],
            temperature=0.5,
            # GIỚI HẠN OUTPUT: Tránh việc model viết quá dài làm tổng token vượt ngưỡng 8000
            max_completion_tokens=1500, 
            top_p=1,
            stream=False 
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Lỗi kết nối AI: {str(e)}"

if __name__ == "__main__":
    test_query = "Cách nấu canh mồng tơi"
    print(f"--- Đang test engine với query: {test_query} ---")
    result = get_rag_recipe(test_query, preference="không ăn cay")
    print(result)