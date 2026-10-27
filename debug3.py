import docker
from dotenv import load_dotenv
load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox-warm-e0d2e96d7f18'})[0]
print(f"容器: {c.name}")

# 直接跑 pip install，不用管道
print("\n=== 手动 pip install matplotlib ===")
ret = c.exec_run(["bash", "-c", "python3 -m pip install --target /workspace/python-packages matplotlib 2>&1"])
print(f"exit_code: {ret.exit_code}")
print("输出前 500 字符:")
print(ret.output.decode()[:500])

client.close()
