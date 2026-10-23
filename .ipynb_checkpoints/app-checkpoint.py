import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ["OMP_NUM_THREADS"] = "4" 
os.environ["MKL_NUM_THREADS"] = "4"
# [修改点 1] 强制关闭底层的 MKL-DNN 加速，避开 Bug
os.environ["FLAGS_use_mkldnn"] = "0" 

import uuid
import threading
import re
from pathlib import Path
from PIL import Image
from flask import Flask, request, jsonify, render_template

from paddleocr import PaddleOCRVL
from openai import OpenAI

# ================= 1. 初始化模型与 API =================
print("[INFO] 正在加载 PaddleOCRVL (放在 CPU 上运行)...")
# [修改点 2] 在初始化参数里，强制加上 enable_mkldnn=False
pipeline = PaddleOCRVL(
    pipeline_version="v1.6", 
    device="cpu",
    enable_mkldnn=False 
)

# 填写你刚才申请的 DeepSeek API Key
DEEPSEEK_API_KEY = "sk-" # ！！！替换成你自己的 Key ！！！

print("[INFO] 正在初始化 DeepSeek 客户端...")
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)
print("[INFO] 初始化完成！")

# 强制指定路径
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
_inference_lock = threading.Lock()

# ================= 2. 核心处理函数 =================
def img_2_txt(model_pipeline, img_path, md_path="output.md"):
    img = Image.open(img_path)
    if max(img.size) > 1000:
        img.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
        img.save(img_path)
    output = model_pipeline.predict(img_path)
    for res in output:
        res.save_to_markdown(md_path)
    return md_path

def read_md_join(filename: str) -> str:
    parts = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            content = line.rstrip("\r\n")
            if content.strip() == "": parts.append("、")
            else: parts.append(content)
    return "".join(parts)

def ask_llm(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的食品合规与健康营养专家，请严格按照用户要求的格式输出，不要废话。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=512
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"API 调用失败: {e}")
        return "API 调用失败，请检查网络或 Key。"

# ================= 3. 提示词工程 =================
PROMPT_EXTRACT = """
请从以下文本中提取食品的配料表。
要求：
1. 必须以“配料表：”开头。
2. 各个配料用中文顿号（、）隔开。
3. 忽略净含量、营养信息、保质期、厂家地址等一切无关信息。
4. 如果没有配料表，输出“配料表：无”。
文本：{ocr_text}
"""

PROMPT_ANALYZE = """
请根据用户的【健康状况】和食品的【配料表】，判断该食品是否适合用户食用。
【健康状况】：{user_condition}
【配料表】：{ingredients}

请严格按以下格式输出：
【食用建议】：(适合 / 慎用 / 不适合 / 严重警告)
【原因分析】：(结合配料和健康情况，给出1-2句话的明确理由)
"""

# ================= 4. 核心业务逻辑 =================
def process_image_and_analyze(img_path: str, user_condition: str) -> dict:
    uid = uuid.uuid4().hex
    md_path = UPLOAD_DIR / f"ocr_{uid}.md"

    with _inference_lock:
        img_2_txt(pipeline, img_path, md_path=str(md_path))
        ocr_text = read_md_join(str(md_path))
        
        extract_prompt = PROMPT_EXTRACT.replace("{ocr_text}", ocr_text[:2000])
        final_ingredients = ask_llm(extract_prompt)
        
        if user_condition.strip():
            analyze_prompt = PROMPT_ANALYZE.replace("{user_condition}", user_condition).replace("{ingredients}", final_ingredients)
            health_advice = ask_llm(analyze_prompt)
        else:
            health_advice = "未提供健康状况，跳过健康评估。"

    try: os.remove(md_path)
    except OSError: pass

    return {"result": final_ingredients, "health_advice": health_advice, "ocr_text": ocr_text}

# ================= 5. 路由 =================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"success": False, "error": "未上传图片文件"}), 400

    file = request.files["image"]
    if file.filename == "": return jsonify({"success": False, "error": "文件名为空"}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT: return jsonify({"success": False, "error": "不支持的文件格式"}), 400

    user_condition = request.form.get("user_condition", "").strip()
    uid = uuid.uuid4().hex
    save_path = UPLOAD_DIR / f"{uid}{ext}"
    file.save(str(save_path))

    try:
        data = process_image_and_analyze(str(save_path), user_condition)
        return jsonify({"success": True, **data})
    except Exception as e:
        app.logger.exception("推理失败")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        try: os.remove(save_path)
        except OSError: pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)