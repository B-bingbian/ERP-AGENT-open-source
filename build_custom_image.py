"""
一键修复：清理旧容器 + 构建预装依赖的自定义镜像
"""
import docker
import tempfile
import os
from dotenv import load_dotenv

load_dotenv()

client = docker.from_env()

# ========== 第一步：清理所有旧沙箱容器 ==========
print("=== 第一步：清理旧容器 ===")
containers = client.containers.list(all=True, filters={'name': 'erp-sandbox'})
print(f"找到 {len(containers)} 个旧容器:")
for c in containers:
    print(f"  - {c.name} ({c.status})")
    c.remove(force=True)
print("已全部清理\n")

# ========== 第二步：构建自定义镜像 ==========
print("=== 第二步：构建自定义镜像（预装依赖）===")
dockerfile_content = """FROM python:3.11-slim
RUN pip install --no-cache-dir matplotlib pandas numpy
RUN python -c "import matplotlib, pandas, numpy; print('deps ok')"
"""

# 写临时 Dockerfile
with tempfile.TemporaryDirectory() as tmpdir:
    dockerfile_path = os.path.join(tmpdir, "Dockerfile")
    with open(dockerfile_path, "w") as f:
        f.write(dockerfile_content)
    
    image, build_logs = client.images.build(
        path=tmpdir,
        tag="erp-sandbox-base:latest",
        rm=True,
    )
    print(f"镜像构建完成: {image.tags}")

# ========== 第三步：验证镜像 ==========
print("\n=== 第三步：验证镜像 ===")
c = client.containers.run(
    image="erp-sandbox-base:latest",
    command="python -c 'import matplotlib; print(\"matplotlib\", matplotlib.__version__)'",
    remove=True,
)
print(f"验证输出: {c.decode().strip()}")

client.close()
print("\n=== 完成！现在可以改配置用新镜像了 ===")
