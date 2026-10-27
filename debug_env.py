import docker
from dotenv import load_dotenv
load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox-warm-2176da5cd622'})[0]
print(f"容器: {c.name}")

# 检查环境变量
print("\n1. PYTHON/PIP 环境变量:")
ret = c.exec_run(["bash", "-c", "env | grep -E 'PYTHON|PIP'"])
print(ret.output.decode())

# 检查 python-packages 目录
print("2. /workspace/python-packages 前 15 项:")
ret = c.exec_run(["bash", "-c", "ls /workspace/python-packages/ | head -15"])
print(ret.output.decode())

# 手动指定 PYTHONPATH 测试
print("3. 手动指定 PYTHONPATH:")
ret = c.exec_run(["bash", "-c", "PYTHONPATH=/workspace/python-packages python -c 'import matplotlib; print(matplotlib.__version__)'"])
print(f"exit={ret.exit_code}")
print(ret.output.decode())

client.close()
