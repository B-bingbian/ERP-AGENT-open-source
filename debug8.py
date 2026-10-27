import docker
from dotenv import load_dotenv
load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox-warm-2a60f9445875'})[0]

print("=== 目录大小 ===")
ret = c.exec_run(["bash", "-c", "du -sh /workspace/python-packages/ 2>&1"])
print(ret.output.decode())

print("=== 手动跑 pip install（这次看真实退出码）===")
# 不用管道，直接看 exit code
ret = c.exec_run(["bash", "-c", "python3 -m pip install --target /workspace/python-packages matplotlib -q && echo PIP_SUCCESS || echo PIP_FAILED"])
print(ret.output.decode())

print("=== 装完后目录大小 ===")
ret = c.exec_run(["bash", "-c", "du -sh /workspace/python-packages/"])
print(ret.output.decode())

client.close()
