"""测试沙箱容器里 pip 安装是否正常"""
import docker
from dotenv import load_dotenv

load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox'})[0]
print(f"测试容器: {c.name}")

# 测试 python -m pip
print("\n1. 测试 python -m pip:")
ret = c.exec_run("python -m pip --version")
print(f"   exit={ret.exit_code}: {ret.output.decode().strip()}")

# 测试安装 matplotlib
print("\n2. 测试安装 matplotlib (超时 30s):")
ret = c.exec_run("python -m pip install --timeout 10 matplotlib 2>&1", )
output = ret.output.decode()
print(f"   exit={ret.exit_code}")
print(f"   输出前 500 字符:\n{output[:500]}")

client.close()
