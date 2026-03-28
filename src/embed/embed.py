import json
from weaviate_client import WeaviateEmbeddingClient

def load_data(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)

    return data

def process_data(data):
    """Chỉ lấy phần text để tạo embedding, có thể mở rộng sau này nếu cần"""
    texts = []
    for item in data:

        recipe_name = item.get("tên món", "")
        ingredients = item.get("nguyên liệu", "")
        instructions = item.get("cách làm", "")
        combined_text = f"{recipe_name}\nNguyên liệu: {ingredients}\nCách làm: {instructions}"
        texts.append({
            "name": recipe_name,
            "ingredients": ingredients,
            "instructions": instructions,
        })

    return texts

if __name__ == "__main__":
    file_path = "../../data/recipe.json"

    data = load_data(file_path)
    embedding_content = process_data(data)

    target_collection = "RecipeDemo"
    with WeaviateEmbeddingClient() as client:
        # 1. Khởi tạo Collection
        client.setup_collection(target_collection)
        
        # 2. Embed content text và lưu kết quả vào CSDL weaviate
        client.embed_and_insert( target_collection, embedding_content)
        
        # 3. Kiểm tra lại dữ liệu đã chèn
        client.verify_data(target_collection)