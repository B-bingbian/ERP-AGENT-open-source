import docker
from dotenv import load_dotenv
load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox-warm-9befe0c582b9'})[0]

print("=== python-packages 目录内容 ===")
ret = c.exec_run(["bash", "-c", "ls /workspace/python-packages/ | head -10"])
print(ret.output.decode())

print("=== 目录大小 ===")
ret = c.exec_run(["bash", "-c", "du -sh /workspace/python-packages/ 2>&1"])
print(ret.output.decode())

print("=== /workspace 挂载选项 ===")
ret = c.exec_run(["bash", "-c", "mount | grep workspace"])
print(ret.output.decode())

client.close()
