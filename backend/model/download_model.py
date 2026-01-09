# download_model.py 修正版
from modelscope.hub.snapshot_download import snapshot_download

# 关键：使用正确的模型仓库名 BAAI/bge-reranker-base
# base 轻量版（推荐，400MB左右）
model_dir = snapshot_download(
    'BAAI/bge-reranker-base', 
    cache_dir='./backend/model/local_models',  # 下载到本地 ./local_models 目录
    revision='master'
)

# 如果需要 large 版（效果更好，1.1GB），替换为：
# model_dir = snapshot_download('BAAI/bge-reranker-large', cache_dir='./local_models')

print(f'模型已下载到：{model_dir}')