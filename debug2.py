import docker
from dotenv import load_dotenv
load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox-warm-e0d2e96d7f18'})[0]

# 看目录结构
print("=== /workspace/python-packages 目录 ===")
ret = c.exec_run(["bash", "-c", "ls -la /workspace/python-packages/ | head -20"])
print(ret.output.decode())

# 手动加 PYTHONPATH 测试
print("=== 手动加 PYTHONPATH 测试 ===")
ret = c.exec_run(["bash", "-c", "PYTHONPATH=/workspace/python-packages python -c 'import sys; print(sys.path); import matplotlib; print(matplotlib.__version__)'"])
print(f"exit={ret.exit_code}")
print(ret.output.decode()[:500])

client.close()
