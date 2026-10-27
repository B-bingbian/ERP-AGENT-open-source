"""验证沙箱依赖是否真的装好了"""
import docker
from dotenv import load_dotenv

load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox-warm'})[0]
print(f"测试容器: {c.name}")

# 看看 python-packages 目录里有什么
print("\n1. /workspace/python-packages 目录内容:")
ret = c.exec_run("ls /workspace/python-packages/ | head -20")
print(f"   {ret.output.decode().strip()}")

# 手动指定 PYTHONPATH 验证
print("\n2. 手动指定 PYTHONPATH 验证:")
ret = c.exec_run(["bash", "-c", "PYTHONPATH=/workspace/python-packages python -c 'import matplotlib; print(\"matplotlib\", matplotlib.__version__)'"])
print(f"   exit={ret.exit_code}")
print(f"   {ret.output.decode().strip()}")

# 测试生成图表
print("\n3. 测试生成图表:")
test_script = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.plot([1,2,3], [4,5,1])
plt.savefig('/workspace/test_chart.png')
print('OK')
"""
ret = c.exec_run(["bash", "-c", f"PYTHONPATH=/workspace/python-packages python -c \"{test_script}\""])
print(f"   exit={ret.exit_code}")
print(f"   {ret.output.decode().strip()[:200]}")

client.close()
