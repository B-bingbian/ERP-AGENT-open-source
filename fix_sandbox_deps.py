"""手动给所有预热容器装上图表依赖"""
import docker
from dotenv import load_dotenv

load_dotenv()

client = docker.from_env()
containers = client.containers.list(filters={'name': 'erp-sandbox-warm'})
print(f"找到 {len(containers)} 个预热容器，开始安装依赖...\n")

install_cmd = """
mkdir -p /workspace/python-packages && \
python3 -m pip install --no-cache-dir --target /workspace/python-packages \
matplotlib pandas numpy 2>&1 | tail -3
"""

for c in containers:
    print(f"[{c.name}] 安装中...")
    ret = c.exec_run(["bash", "-c", install_cmd])
    output = ret.output.decode().strip()
    if ret.exit_code == 0:
        print(f"  ✅ 安装成功")
        # 验证
        verify = c.exec_run(["python", "-c", "import matplotlib; print('matplotlib', matplotlib.__version__)"])
        if verify.exit_code == 0:
            print(f"  ✅ 验证通过: {verify.output.decode().strip()}")
        else:
            print(f"  ⚠️ 验证失败: {verify.output.decode().strip()[:100]}")
    else:
        print(f"  ❌ 安装失败 (exit {ret.exit_code})")
        print(f"     {output[:300]}")
    print()

client.close()
print("=== 完成 ===")
