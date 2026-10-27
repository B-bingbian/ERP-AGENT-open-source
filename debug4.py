import docker
from dotenv import load_dotenv
load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox-warm-e0d2e96d7f18'})[0]

# 看完整错误，只看最后 30 行
ret = c.exec_run(["bash", "-c", "python3 -m pip install --target /workspace/python-packages matplotlib 2>&1 | tail -30"])
print(ret.output.decode())

client.close()
