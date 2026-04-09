from sympy import vector
import weaviate
from weaviate.classes.config import Configure
from sentence_transformers import SentenceTransformer
import torch
import os
class WeaviateEmbeddingClient:
    def __init__(self, model_name="BAAI/bge-m3"):
        self.model_name = model_name
        self._model = None  # Ban đầu chưa load model
        print("Đang kết nối tới Weaviate...")
        # Sử dụng connect_to_local() của v4
        self.client = weaviate.connect_to_custom(
        http_host=os.getenv("WEAVIATE_HOST", "localhost"),
        http_port=8080,
        http_secure=False,
        grpc_host=os.getenv("WEAVIATE_HOST", "localhost"),
        grpc_port=50051,
        grpc_secure=False
)

    @property
    def model(self):
        """Chỉ load model khi thực sự cần dùng đến (Lazy Loading)"""
        if self._model is None:
            print(f"--- Đang tải model {self.model_name} vào RAM (Chỉ tải 1 lần) ---")
            # Kiểm tra xem có GPU không, nếu không dùng CPU
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model = SentenceTransformer(self.model_name, device=device)
        return self._model

    def embed_and_insert(self, collection_name, texts, batch_size=16):
        """Tạo đối tượng vector và chèn vào database Weaviate
        Args: texts: 1 list các dict có key là "name", "ingredients", "instructions"
              Hoặc 1 string (đối với test đơn giản).
        """
        from weaviate.classes.data import DataObject
        
        # Chuẩn hóa đầu vào để code có thể hoạt động với cả list dict và string đơn lẻ
        if isinstance(texts, str):
            texts = [{"name": texts, "ingredients": "", "instructions": ""}]
            
        if not texts:
            return

        collection = self.client.collections.get(collection_name)
        total_inserted = 0

        # Xử lý theo từng batch để tối ưu tốc độ và bộ nhớ
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Ghép văn bản cho embedding
            texts_to_embed = []
            for item in batch:
                combined_text = item.get('name', '')
                if item.get('ingredients'):
                    combined_text += f"\nNguyên liệu: {item['ingredients']}"
                if item.get('instructions'):
                    combined_text += f"\nCách làm: {item['instructions']}"
                # print(combined_text)  # In ra nội dung text trước khi embed để kiểm tra
                texts_to_embed.append(combined_text)

            # Chạy encode theo batch trên SentenceTransformer
            embeddings = self.model.encode(texts_to_embed) 
            
            # Chuẩn bị danh sách DataObject để insert_many (tối ưu Weaviate)
            data_objects = []
            for item, emb in zip(batch, embeddings):
                data_objects.append(
                    DataObject(
                        properties=item, # Lưu toàn bộ dict vào properties
                        vector=emb.tolist()
                    )
                )
                
            # Insert vào Weaviate 1 lần cho cả batch
            collection.data.insert_many(data_objects)
            total_inserted += len(data_objects)
            print(f"Đã lưu {total_inserted}/{len(texts)} đối tượng...")
            
        print("Lưu dữ liệu thành công!")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def setup_collection(self, collection_name):
        """Chỉ tạo Collection nếu nó chưa tồn tại, không xóa dữ liệu cũ"""
        if self.client.collections.exists(collection_name):
            print(f"Collection '{collection_name}' đã tồn tại. Bỏ qua bước tạo mới.")
            return self.client.collections.get(collection_name)
            
        print(f"Đang tạo mới collection '{collection_name}'...")
        collection = self.client.collections.create(
            name=collection_name,
            vectorizer_config=Configure.Vectorizer.none() 
        )
        return collection

    def retrieve_similar(self, collection_name, query_text, top_k=5):
        """Truy vấn tìm kiếm các đối tượng tương tự dựa trên vector embedding"""
        collection = self.client.collections.get(collection_name)
        
        # Tạo embedding cho query
        query_embedding = self.model.encode([query_text])[0]
        
        # Thực hiện truy vấn tìm kiếm tương tự
        response = collection.query.hybrid(
            query=query_text,  # Truy vấn văn bản để kết hợp với vector
            vector=query_embedding.tolist(),
            limit=top_k,

        )
        return response.objects
        
        
    def verify_data(self, collection_name):
        """Kiểm tra xuất dữ liệu sau khi chèn"""
        collection = self.client.collections.get(collection_name)
        print("\n--- Đang truy xuất lại từ Weaviate ---")
        response = collection.query.fetch_objects(limit=1, include_vector=True)
        for item in response.objects:
            print(f"Nội dung text lấy ra: {item.properties.get('text')}")
            print(f"Vector (hiển thị 5 chiều đầu tiên): {item.vector['default'][:5]}")

    def list_collections(self):
        """Liệt kê tất cả các collection hiện có trong Weaviate (v4)"""
        # list_all() trả về dict: { "CollectionName": CollectionObject, ... }
        collections = self.client.collections.list_all()
        
        print("\n--- Danh sách Collections trong Weaviate ---")
        if not collections:
            print("Hiện chưa có collection nào.")
        else:
            for name in collections.keys():
                print(f"- {name}")
    
        return list(collections.keys()) 
    
    def peek_objects(self, collection_name, limit=5):
        """Xem thử một số object trong collection để kiểm tra dữ liệu đã chèn có đúng không"""
        print(f"\n--- Peek thử {limit} object trong collection '{collection_name}' ---")
        collection = self.client.collections.get(collection_name)
        
        # fetch_objects cho phép lấy kèm theo Vector nếu muốn
        response = collection.query.fetch_objects(
            limit=limit,
            include_vector=True  # Xem thử vector BGE-M3 có tồn tại không
        )

        for obj in response.objects:
            print(obj.properties)  # In ra tất cả properties của object

    def delete_collection(self, collection_name):
        """Xóa một collection cụ thể trong Weaviate"""
        if self.client.collections.exists(collection_name):
            self.client.collections.delete(collection_name)
            print(f"Collection '{collection_name}' đã được xóa.")
        else:
            print(f"Collection '{collection_name}' không tồn tại.")
    def close(self):
        """Đóng kết nối cơ sở dữ liệu"""
        self.client.close()
        print("Đã đóng kết nối với Weaviate.")


# if __name__ == "__main__":
#     sample_text = "Đây là test 123."
#     target_collection = "RecipeDemo"
    
#     # Sử dụng context manager (with) để đảm bảo kết nối luôn đóng thông qua hàm __exit__
#     with WeaviateEmbeddingClient() as client:
#         # 1. Khởi tạo Collection
#         # client.setup_collection(target_collection)
        
#         # # 2. Embed content text và lưu kết quả vào CSDL weaviate
#         # client.embed_and_insert(target_collection, sample_text)
        
#         # # 3. Kiểm tra bằng cách fetch từ CSDL về
#         # client.verify_data(target_collection)
        
#         # # 4. Liệt kê tất cả các collection
#         # client.list_collections()
        
#         # 5. Xóa collection
#         # client.delete_collection(target_collection)

#         # 6. Peek thử một số object trong collection
#         # client.peek_objects(target_collection, limit=3)

#         # 7. Retrieve similar 
#         query = "Tôi muốn tìm công thức nấu ăn canh mồng tơi nấu đậu phụ và rong kombu"
#         response = client.retrieve_similar(target_collection, query_text=query, top_k=3)
#         print("\n--- Kết quả truy vấn tương tự ---")
#         for idx, item in enumerate(response):
#             # print(f"{idx+1}. {item.properties.get('name', 'N/A')} (Similarity Score: {item.similarity_score:.4f})")
#             print(f"   Tên món: {item.properties.get('name', 'N/A')}")
#             print(f"   Nguyên liệu: {item.properties.get('ingredients', 'N/A')}")
#             print(f"   Cách làm: {item.properties.get('instructions', 'N/A')}\n")
#             print(f"="*20)

if __name__ == "__main__":
    target_collection = "RecipeDemo"
    
    with WeaviateEmbeddingClient() as client:
        # --- KIỂM TRA 1: Liệt kê các kho đang có ---
        client.list_collections()

        # --- KIỂM TRA 2: Soi thử nội dung 3 món đầu tiên ---
        # (Để xem name, ingredients có bị None hay không)
        client.peek_objects(target_collection, limit=3)

        # --- KIỂM TRA 3: Test độ thông minh (RAG Test) ---
        query = "món canh nào mát cho mùa hè có đậu phụ"
        print(f"\n--- Đang thử tìm kiếm ý nghĩa: '{query}' ---")
        
        response = client.retrieve_similar(target_collection, query_text=query, top_k=2)
        
        if not response:
            print("❌ Không tìm thấy gì. Có thể dữ liệu chưa vào hoặc collection sai tên.")
        else:
            for idx, item in enumerate(response):
                print(f"{idx+1}. Tên món: {item.properties.get('name')}")
                print(f"   Lý do chọn: Vì có nguyên liệu [{item.properties.get('ingredients')[:50]}...]")
                print("-" * 30)