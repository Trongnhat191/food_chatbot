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

    # 1. Truy vấn ngữ cảnh từ Weaviate - Tăng top_k lên 3 để AI có nhiều lựa chọn hơn
    with WeaviateEmbeddingClient() as client:
        retrieve_context = client.retrieve_similar(
            os.getenv("WEAVIATE_COLLECTION", "RecipeDemo"), 
            query_text=query, 
            top_k=3 
        )
        
    if not retrieve_context:
        return None

    context_text = ""
    for obj in retrieve_context:
        name = obj.properties.get('name', '')[:200]
        ingredients = obj.properties.get('ingredients', '')[:1500]
        instructions = obj.properties.get('instructions', '')[:2000]
        
        context_text += (
            f"Tên món: {name}\n"
            f"Nguyên liệu: {ingredients}\n"
            f"Cách làm: {instructions}\n"
            f"--- Kết thúc một món ---\n\n"
        )

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # CẬP NHẬT SYSTEM PROMPT: Cho phép AI tính toán định lượng
    system_prompt = (
        "Bạn là đầu bếp trợ lý ảo chuyên nghiệp. Nhiệm vụ của bạn:\n"
        "1. Nếu người dùng liệt kê nguyên liệu: Hãy gợi ý 2-3 tên món phù hợp.\n"
        "2. Nếu người dùng hỏi cách nấu hoặc tìm món cụ thể: Hãy liệt kê nguyên liệu và các bước làm.\n"
        "3. QUY ĐỊNH ĐỊNH LƯỢNG: Nếu người dùng yêu cầu cho một số lượng người cụ thể (ví dụ: 4 người), "
        "hãy dựa vào định lượng trong dữ liệu gốc và TỰ ĐỘNG TÍNH TOÁN LẠI (Scale) các con số nguyên liệu "
        "cho phù hợp với số người đó. Đừng máy móc chép lại con số sai lệch.\n"
        "4. QUY ĐỊNH ĐỊNH DẠNG: Ngăn cách mỗi bước nấu bằng dấu '|'. Ví dụ: Bước 1... | Bước 2...\n"
        "5. Nếu là gợi ý món, dùng dấu '-' để liệt kê."
    )

    try:
        completion = client.chat.completions.create(
            model=os.getenv("MODEL_NAME"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Dữ liệu gốc:\n{context_text}\n\nCâu hỏi của người dùng: {query}"}
            ],
            temperature=0.4, # Giảm nhiệt độ xuống một chút để tính toán chính xác hơn
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