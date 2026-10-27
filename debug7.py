import docker
from dotenv import load_dotenv
load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox-warm-a03fa65da82a'})[0]

print("=== 磁盘使用情况 ===")
ret = c.exec_run(["bash", "-c", "df -h"])
print(ret.output.decode())

print("=== /workspace 大小 ===")
ret = c.exec_run(["bash", "-c", "df -h /workspace"])
print(ret.output.decode())

client.close()
