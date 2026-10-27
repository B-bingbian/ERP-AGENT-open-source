import docker
from dotenv import load_dotenv
load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox-warm'})[0]
print(f"容器: {c.name}")

# 列目录
ret = c.exec_run("ls -la /workspace/python-packages/")
print("ls /workspace/python-packages/:")
print(ret.output.decode())

# 看看 pip 装到哪了
ret = c.exec_run("python3 -m pip show matplotlib --target /workspace/python-packages 2>&1 | head -10")
print("\npip show:")
print(ret.output.decode())

client.close()
