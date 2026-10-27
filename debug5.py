import docker
from dotenv import load_dotenv
load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox-warm-a03fa65da82a'})[0]

print("=== python-packages 目录内容 ===")
ret = c.exec_run(["bash", "-c", "ls -lh /workspace/python-packages/ | head -20"])
print(ret.output.decode())

print("=== 目录大小 ===")
ret = c.exec_run(["bash", "-c", "du -sh /workspace/python-packages/"])
print(ret.output.decode())

print("=== 手动 PYTHONPATH 测试 ===")
ret = c.exec_run(["bash", "-c", "PYTHONPATH=/workspace/python-packages python -c 'import matplotlib; print(matplotlib.__version__)'"])
print(f"exit={ret.exit_code}")
print(ret.output.decode()[:200])

client.close()
