# 🍲 Recipe Chatbot

## 📂 Cấu trúc thư mục

- `data/recipe.json`: Dữ liệu chứa các công thức nấu ăn.
- `src/docker-compose.yml`: File cấu hình Docker để khởi chạy cơ sở dữ liệu Weaviate.
- `src/embed/embed.py`: Script xử lý và nhúng (embed) dữ liệu công thức vào Weaviate.
- `src/embed/weaviate_client.py`: Client kết nối và tương tác với Weaviate.
- `src/weaviate_data/`: Thư mục lưu trữ persistence data cục bộ của Weaviate.

## 🚀 Hướng dẫn cài đặt và sử dụng

### 1. Yêu cầu hệ thống

- Tải và cài đặt [Docker](https://www.docker.com/) cùng hệ thống Docker Compose.
- Phiên bản Python 3.8 trở lên.

### 2. Khởi chạy Weaviate Vector Database

Sử dụng Docker Compose để khởi chạy Weaviate ở dưới dạng background:

```bash
cd src
docker-compose up -d
```

### 3. Thiết lập môi trường Python (sử dụng uv)

Dự án này sử dụng trình quản lý package [uv](https://github.com/astral-sh/uv) để cài đặt nhanh chóng và quản lý thư viện.

```bash
# Đồng bộ và tự động tạo môi trường cài đặt tất cả thư viện (đòi hỏi pyproject.toml hoặc requirements.txt nếu được cấu hình)
uv sync

# Kích hoạt môi trường (tuỳ chọn nếu bạn muốn dùng python trần trực tiếp, hoặc có thể dùng `uv run`)
source .venv/bin/activate
```

### 4. Nhúng (Embed) dữ liệu vào Weaviate

Đọc dữ liệu từ recipe.json và lưu trữ dưới dạng vector vào CSDL bằng

```bash
python src/embed/embed.py
```

### 5. Sử dụng phần Chat (Chat)

- **Mô tả:** file `src/chat/chat.py` là entry point cho phần chat. Khi chạy, script sẽ lấy ngữ cảnh tương tự từ Weaviate rồi gọi API Groq để tạo phản hồi (streaming).

- **Biến môi trường cần thiết:** tạo file `.env` tại thư mục gốc với các biến sau:

```
GROQ_API_KEY=your_groq_api_key
MODEL_NAME=your_model_name
WEAVIATE_COLLECTION=your_collection_name
```

# Chạy chat (từ gốc repo). Khuyến nghị dùng module run để tránh lỗi import:
python -m src.chat.chat

# Hoặc với uv:
uv run python -m src.chat.chat
```

- **Ghi chú & lỗi thường gặp:**
  - Nếu gặp `ModuleNotFoundError: No module named 'embed'`, hãy chạy bằng cách `python -m src.chat.chat` từ thư mục gốc hoặc đảm bảo `PYTHONPATH` có chứa thư mục `src`.
  - `src/chat/chat.py` hiện có một truy vấn mẫu ở cuối file; để thử query khác, sửa biến `query` trong khối `if __name__ == "__main__":` hoặc chuyển sang giao diện tương tác tùy bạn.
