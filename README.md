# Auto Cut Picture

一个智能图片裁剪和重新构图的 Web 应用，支持 AI 智能构图分析。

## 功能特性

- 📷 **多图片上传**：支持拖拽上传 PNG、JPG、JPEG、WebP、GIF 格式图片
- ✂️ **智能裁剪**：交互式裁剪框，支持多种预设宽高比
- 🤖 **AI 智能构图**：基于阿里云百炼 Qwen-VL-Plus 的智能构图分析
- 📐 **多版本管理**：每张图片支持创建多个裁剪版本
- 🔄 **批量处理**：一键处理所有版本
- 📥 **批量导出**：支持 ZIP 打包下载
- 📋 **EXIF 保留**：保留原图的 EXIF 信息

## 技术栈

### 前端
- **Next.js 14** - React 框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式
- **Zustand** - 状态管理
- **react-dropzone** - 文件上传

### 后端
- **Python 3.13+**
- **FastAPI** - Web 框架
- **Pillow** - 图片处理
- **Qwen-VL-Plus** - AI 智能构图分析（阿里云百炼）

## 项目结构

```
.
├── frontend/                 # Next.js 前端
│   ├── src/
│   │   ├── app/             # 页面组件
│   │   ├── components/      # UI 组件
│   │   ├── hooks/           # React Hooks
│   │   └── lib/             # 工具库
│   ├── public/              # 静态资源
│   └── package.json
│
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── api/             # API 路由
│   │   ├── config/          # 配置
│   │   ├── models.py        # 数据模型
│   │   └── services/        # 业务逻辑
│   └── requirements.txt
│
└── storage/                  # 文件存储
    ├── uploads/             # 原始图片
    ├── processed/           # 处理后的图片
    └── thumbnails/          # 缩略图
```

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.13+
- 阿里云百炼 API Key（用于 AI 智能构图）

### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 QWEN_API_KEY

# 启动服务
uvicorn app.main:app --reload --port 8000
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:3000 开始使用。

## 配置

### 后端环境变量

在 `backend/.env` 文件中配置：

```env
# 前端 URL（用于 CORS）
FRONTEND_URL=http://localhost:3000

# 阿里云百炼 API 配置
QWEN_API_KEY=your_api_key_here
QWEN_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
QWEN_MODEL=qwen3-vl-plus

# 存储路径
STORAGE_PATH=./storage
```

### 预设宽高比

支持以下预设宽高比：

| 预设 | 宽高比 | 用途 |
|------|--------|------|
| Square | 1:1 | 社交媒体 |
| Landscape 4:3 | 4:3 | 传统照片 |
| Landscape 16:9 | 16:9 | 视频/显示器 |
| Portrait 3:4 | 3:4 | 人像 |
| Portrait 9:16 | 9:16 | 竖屏视频/手机 |
| Story | 9:16 | Instagram Story |
| Twitter Header | 3:1 | Twitter 头图 |
| Facebook Cover | 2.7:1 | Facebook 封面 |
| Freeform | - | 自由比例 |

## API 接口

### 图片管理

- `POST /api/images/upload` - 上传图片
- `GET /api/images` - 获取所有图片
- `GET /api/images/{image_id}` - 获取单个图片
- `DELETE /api/images/{image_id}` - 删除图片
- `DELETE /api/images` - 删除所有图片

### 版本管理

- `GET /api/images/{image_id}/versions` - 获取图片的所有版本
- `POST /api/images/{image_id}/versions` - 创建新版本
- `DELETE /api/images/{image_id}/versions/{version_id}` - 删除版本
- `POST /api/images/{image_id}/versions/{version_id}/crop` - 更新裁剪数据

### 处理与导出

- `POST /api/images/{image_id}/analyze` - AI 智能构图分析
- `POST /api/images/batch-process` - 批量处理
- `GET /api/images/{image_id}/versions/{version_id}/download` - 下载单个版本
- `POST /api/images/batch-download` - 批量下载（ZIP）

## 使用说明

1. **上传图片**：拖拽或点击上传图片
2. **选择图片**：从左侧图片列表选择要编辑的图片
3. **创建版本**：点击 "New Version" 创建新的裁剪版本
4. **选择预设**：从右侧选择预设宽高比
5. **调整裁剪框**：拖动裁剪框调整位置和大小
6. **智能分析**：点击 "Smart Analyze" 使用 AI 推荐构图
7. **处理导出**：点击 "Process All Versions" 处理，然后下载

## 开发

### 前端构建

```bash
cd frontend
npm run build
npm run start
```

### 后端生产模式

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 许可证

MIT License