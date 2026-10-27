import docker
from dotenv import load_dotenv
load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox-warm-2176da5cd622'})[0]
print(f"容器: {c.name}")

# 手动跑 pip install，看完整输出
print("\n手动安装 matplotlib:")
ret = c.exec_run([
    "bash", "-c",
    "python3 -m pip install --target /workspace/python-packages matplotlib 2>&1"
])
print(f"exit_code: {ret.exit_code}")
print("输出:")
print(ret.output.decode()[:800])

client.close()
