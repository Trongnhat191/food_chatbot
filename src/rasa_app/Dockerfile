# Sử dụng Python slim để tối ưu dung lượng (khoảng 150MB thay vì 1GB)
FROM python:3.10-slim

# Bước 1: Cài đặt uv - trình quản lý gói siêu tốc mà Minh đang dùng
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Bước 2: Thiết lập thư mục làm việc
WORKDIR /app

# Bước 3: Cài đặt các thư viện cần thiết
# Lưu ý: Cài torch phiên bản CPU-only để tiết kiệm RAM và dung lượng (vì máy Minh không có GPU)
RUN uv pip install --system --no-cache \
    rasa-sdk==3.6.2 \
    groq \
    weaviate-client \
    sentence-transformers \
    torch --index-url https://download.pytorch.org/whl/cpu \
    python-dotenv

# Bước 4: Copy mã nguồn vào container
# Chúng ta copy folder rasa_app vào /app
COPY ./src/rasa_app /app
# Copy thêm folder chat và embed để actions.py có thể import (Hướng B & C)
COPY ./src/chat /app/src/chat
COPY ./src/embed /app/src/embed

# Bước 5: Thiết lập PYTHONPATH để Python hiểu cấu trúc thư mục src.xxx
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Bước 6: Khai báo Port cho Action Server
EXPOSE 5055

# Bước 7: Chạy Action Server khi container khởi động
# --actions actions: chỉ định thư mục chứa file actions.py
USER 1001
ENTRYPOINT ["rasa", "run", "actions", "--actions", "actions"]