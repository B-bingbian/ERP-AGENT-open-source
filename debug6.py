import docker
from dotenv import load_dotenv
load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox-warm-a03fa65da82a'})[0]

print("=== 手动 pip install（完整错误）===")
ret = c.exec_run(["bash", "-c", "python3 -m pip install --target /workspace/python-packages matplotlib pandas numpy 2>&1 | tail -15"])
print(ret.output.decode())

client.close()
