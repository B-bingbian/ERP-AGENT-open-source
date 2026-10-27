"""手动给预热容器装依赖并验证"""
import docker
from dotenv import load_dotenv

load_dotenv()

client = docker.from_env()
containers = client.containers.list(filters={'name': 'erp-sandbox-warm'})
print(f"找到 {len(containers)} 个预热容器\n")

for c in containers:
    print(f"=== {c.name} ===")
    
    # 检查是否已经装了
    ret = c.exec_run(["bash", "-c", "ls /workspace/python-packages/matplotlib 2>/dev/null && echo HAS_MATPLOTLIB || echo NO_MATPLOTLIB"])
    if "HAS_MATPLOTLIB" in ret.output.decode():
        print("  已装，跳过")
        continue
    
    # 安装
    print("  安装中...")
    ret = c.exec_run([
        "bash", "-c",
        "python3 -m pip install --target /workspace/python-packages matplotlib pandas numpy -q 2>&1 | tail -5; echo EXIT_CODE=$?"
    ])
    output = ret.output.decode()
    print(f"  {output.strip()}")

# 验证最新的那个
print("\n=== 验证 ===")
c = containers[0]
ret = c.exec_run(["python", "-c", "import matplotlib; print('matplotlib', matplotlib.__version__)"])
if ret.exit_code == 0:
    print(f"  ✅ import 成功: {ret.output.decode().strip()}")
else:
    print(f"  ❌ import 失败: {ret.output.decode().strip()[:200]}")

client.close()
