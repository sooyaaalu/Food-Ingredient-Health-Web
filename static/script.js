const dropArea = document.getElementById('dropArea');
const fileInput = document.getElementById('fileInput');
const preview = document.getElementById('preview');
const submitBtn = document.getElementById('submitBtn');
const loading = document.getElementById('loading');
const resultBox = document.getElementById('resultBox');
const resultText = document.getElementById('resultText');
const adviceText = document.getElementById('adviceText');
const errorBox = document.getElementById('errorBox');
const uploadInner = document.getElementById('uploadInner');
const userCondition = document.getElementById('userCondition');

let currentFile = null;

function setFile(file) {
  if (!file) return;
  currentFile = file;
  preview.src = URL.createObjectURL(file);
  preview.style.display = 'block';
  uploadInner.style.display = 'none';
  submitBtn.disabled = false;
  resultBox.style.display = 'none';
  errorBox.style.display = 'none';
}

dropArea.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => setFile(e.target.files[0]));

dropArea.addEventListener('dragover', e => { e.preventDefault(); dropArea.classList.add('dragging'); });
dropArea.addEventListener('dragleave', e => { e.preventDefault(); dropArea.classList.remove('dragging'); });
dropArea.addEventListener('drop', e => {
  e.preventDefault(); 
  dropArea.classList.remove('dragging');
  setFile(e.dataTransfer.files[0]);
});

submitBtn.addEventListener('click', async () => {
  if (!currentFile) return;
  loading.style.display = 'flex';
  submitBtn.disabled = true;
  resultBox.style.display = 'none';
  errorBox.style.display = 'none';

  const loadingText = loading.querySelector('span'); 
  loadingText.textContent = "正在识别图片文字（本地处理中，稍安勿躁）...";
  
  // 设个定时器，如果过了 8 秒还没出结果，文字自动变成“DeepSeek分析中”
  const textTimer = setTimeout(() => {
    loadingText.textContent = "正在由 DeepSeek 进行深度健康分析...";
  }, 8000); 
    
  const formData = new FormData();
  formData.append('image', currentFile);
  formData.append('user_condition', userCondition.value);

  try {
    const resp = await fetch('/api/predict', { method: 'POST', body: formData });
    const data = await resp.json();
    
    if (!resp.ok || !data.success) throw new Error(data.error || '识别失败');
    
    resultText.textContent = data.result || '(空)';
    adviceText.textContent = data.health_advice || '未提供健康状况';
    resultBox.style.display = 'block';
  } catch (err) {
    errorBox.textContent = '❌ ' + err.message;
    errorBox.style.display = 'block';
  } finally {
    loading.style.display = 'none';
    submitBtn.disabled = false;
  }
})