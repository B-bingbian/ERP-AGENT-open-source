"""对比测试：seccomp 是否导致容器不能联网"""
import docker
from dotenv import load_dotenv

load_dotenv()

client = docker.from_env()

# 测试命令：尝试连 pypi
test_cmd = ["bash", "-c", "python -c 'import urllib.request; urllib.request.urlopen(\"https://pypi.org\", timeout=5); print(\"NET OK\")' 2>&1"]

# 测试 1：用项目同款安全配置（开 seccomp）
print("=== 测试1：项目默认安全配置（seccomp 开）===")
c1 = client.containers.run(
    image="python:3.11-slim",
    name="test-seccomp-on",
    command="sleep infinity",
    detach=True,
    network_mode="bridge",
    cap_drop=["ALL"],
    security_opt=["no-new-privileges:true"],
)
import time; time.sleep(1)
ret = c1.exec_run(test_cmd)
print(f"exit={ret.exit_code}")
print(ret.output.decode().strip()[:300])

# 测试 2：关 seccomp
print("\n=== 测试2：seccomp 关闭 ===")
c2 = client.containers.run(
    image="python:3.11-slim",
    name="test-seccomp-off",
    command="sleep infinity",
    detach=True,
    network_mode="bridge",
    cap_drop=["ALL"],
    security_opt=["no-new-privileges:true", "seccomp=unconfined"],
)
time.sleep(1)
ret = c2.exec_run(test_cmd)
print(f"exit={ret.exit_code}")
print(ret.output.decode().strip()[:300])

# 清理
c1.remove(force=True)
c2.remove(force=True)
print("\n测试容器已清理")

client.close()
