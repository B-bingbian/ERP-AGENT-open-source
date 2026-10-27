"""快速测试沙箱容器状态和依赖"""
import docker
import os
from dotenv import load_dotenv

load_dotenv()

client = docker.from_env()
print(f"Docker 连接成功: {client.version()['Version']}")

# 找运行中的沙箱容器
containers = client.containers.list(filters={'name': 'erp-sandbox'})
print(f"\n找到 {len(containers)} 个运行中的沙箱容器:")
for c in containers:
    print(f"  - {c.name} ({c.status})")

if not containers:
    print("❌ 没有找到运行中的沙箱容器")
    exit(1)

# 测试第一个容器
c = containers[0]
print(f"\n=== 测试容器: {c.name} ===")

# 1. Python 版本
ret = c.exec_run("python --version")
print(f"✅ Python: {ret.output.decode().strip()}")

# 2. matplotlib
ret = c.exec_run("python -c 'import matplotlib; print(matplotlib.__version__)'")
if ret.exit_code == 0:
    print(f"✅ matplotlib: {ret.output.decode().strip()}")
else:
    print(f"❌ matplotlib: 未安装")
    print(f"   错误: {ret.output.decode().strip()[:150]}")

# 3. pandas
ret = c.exec_run("python -c 'import pandas; print(pandas.__version__)'")
if ret.exit_code == 0:
    print(f"✅ pandas: {ret.output.decode().strip()}")
else:
    print(f"❌ pandas: 未安装")

# 4. 测试生成图表（模拟真实调用）
test_script = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.plot([1,2,3], [4,5,1])
plt.savefig('/workspace/test_chart.png')
print('图表生成成功: /workspace/test_chart.png')
"""
ret = c.exec_run(["python", "-c", test_script])
if ret.exit_code == 0:
    print(f"✅ 图表生成测试: {ret.output.decode().strip()}")
else:
    print(f"❌ 图表生成失败 (exit {ret.exit_code})")
    print(f"   错误: {ret.output.decode().strip()[:300]}")

client.close()
print("\n=== 测试完成 ===")
