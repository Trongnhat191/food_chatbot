# Sử dụng Python slim để tối ưu dung lượng
FROM python:3.10-slim

# Bước 1: Cài đặt uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Bước 2: Thiết lập thư mục làm việc
WORKDIR /app

# Bước 3: Cài đặt các thư viện cần thiết
RUN uv pip install --system --no-cache \
    rasa-sdk==3.6.2 \
    groq \
    weaviate-client \
    sentence-transformers \
    python-dotenv

# Bước 4: Cài đặt riêng torch CPU
RUN uv pip install --system --no-cache \
    torch --index-url https://download.pytorch.org/whl/cpu

# --- BƯỚC QUAN TRỌNG: TẢI SẴN MODEL VÀO IMAGE ---
# Mình đặt các biến ENV trước để model được tải đúng vào thư mục cache này
ENV TRANSFORMERS_CACHE="/tmp/transformers_cache"
ENV TORCH_HOME="/tmp/torch_cache"

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"
# -----------------------------------------------

# Bước 5: Copy mã nguồn vào container
COPY ./src/rasa_app /app
COPY ./src/chat /app/src/chat
COPY ./src/embed /app/src/embed

# Bước 6: Thiết lập PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Bước 7: Khai báo Port và Chạy Action Server
EXPOSE 5055
ENTRYPOINT ["python", "-m", "rasa_sdk", "--actions", "actions"]