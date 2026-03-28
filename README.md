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

### 3. Thiết lập môi trường Python

### 4. Nhúng (Embed) dữ liệu vào Weaviate
Đọc dữ liệu từ recipe.json và lưu trữ dưới dạng vector vào CSDL bằng
```bash
python src/embed/embed.py
```