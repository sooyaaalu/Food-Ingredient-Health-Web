# 🍎 食品配料表与健康分析系统 (Food Ingredient & Health Analyzer)

基于本地 PaddleOCR 与云端 DeepSeek 大模型的智能健康助手。用户只需上传食品配料表图片，并输入个人健康状况（如高血压、长痘、过敏等），系统即可自动提取配料，并给出专业的食用建议和医学原因分析。

## ✨ 核心功能
- **高精度 OCR 识别**：采用 PaddleOCR 本地 CPU 识别，支持复杂排版。
- **深度健康分析**：接入 DeepSeek API，结合医学常识和配料成分进行推理。
- **清爽前端交互**：原生 HTML/CSS/JS 开发，支持拖拽上传。
- **隐私安全**：API Key 采用环境变量注入，不泄露。

## 🛠️ 技术栈
- **前端**：HTML5, CSS3, JavaScript (Fetch API)
- **后端**：Python, Flask
- **AI 组件**：PaddleOCR (本地运行), DeepSeek-V3 API (云端)

## 🚀 本地运行指南
1. 克隆项目并进入目录
2. 安装依赖：`pip install flask paddleocr openai pillow`
3. 配置环境变量：`export DEEPSEEK_API_KEY="你的真实Key"`
4. 启动服务：`python app.py`
5. 浏览器访问 `http://127.0.0.1:5000`
