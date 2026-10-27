import docker
from dotenv import load_dotenv

load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox-warm-b2b208512916'})[0]

print("=== df -h ===")
ret = c.exec_run(["bash", "-c", "df -h"])
print(ret.output.decode())

print("=== ls /tmp ===")
ret = c.exec_run(["bash", "-c", "ls -la /tmp/"])
print(ret.output.decode())

client.close()
