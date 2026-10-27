import docker
from dotenv import load_dotenv

load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox-warm-b2b208512916'})[0]

print(f"容器: {c.name}")
print(f"镜像: {c.image.tags[0]}")
print(f"状态: {c.status}")

# 看容器的挂载和 read-only 设置
attrs = c.attrs
print(f"\nRead-only rootfs: {attrs['HostConfig']['ReadonlyRootfs']}")
print(f"\n挂载信息:")
for mount in attrs['Mounts']:
    print(f"  - {mount['Source']} -> {mount['Destination']} ({mount['Type']})")

# 测试能不能写 /tmp
print("\n测试写 /tmp:")
ret = c.exec_run(["bash", "-c", "echo 'test' > /tmp/test.txt && cat /tmp/test.txt && echo WRITE_OK"])
print(f"  exit={ret.exit_code}")
print(f"  {ret.output.decode().strip()}")

client.close()
