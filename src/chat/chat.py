import sys
import os

# Thêm thư mục 'src' vào sys.path để có thể import các module bên trong src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from dotenv import load_dotenv
from typer import completion
from embed.weaviate_client import WeaviateEmbeddingClient
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
WEAVIATE_COLLECTION = os.getenv("WEAVIATE_COLLECTION")


def client_chat(query):
    with WeaviateEmbeddingClient() as client:
        retrieve_context = client.retrieve_similar(WEAVIATE_COLLECTION, query_text=query, top_k=1)
    client = Groq(api_key=API_KEY)
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "Bạn là một trợ lý ảo giúp người dùng tìm kiếm công thức nấu ăn dựa trên các nguyên liệu họ có. Bạn sẽ sử dụng thông tin từ cơ sở dữ liệu để đưa ra các gợi ý công thức phù hợp nhất.\n Lưu ý: Trả lời ngắn gọn, súc tích, tập trung vào công thức nấu ăn và nguyên liệu liên quan đến truy vấn của người dùng. Nếu không tìm thấy công thức phù hợp, hãy trả lời rằng bạn không có thông tin cần thiết để giúp đỡ."
            },
            {
                "role": "user",
                "content": f"{retrieve_context}\n\n{query}"
            }
        ],
        temperature=1,
        max_completion_tokens=8192,
        top_p=1,
        reasoning_effort="medium",
        stream=True,
        stop=None
    )

    for chunk in completion:
        print(chunk.choices[0].delta.content or "", end="")

if __name__ == "__main__":
    query = "Tôi muốn tìm công thức nấu ăn canh mồng tơi nấu đậu phụ và rong kombu"
    client_chat(query)
