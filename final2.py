import docker
from dotenv import load_dotenv
load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox-warm-a03fa65da82a'})[0]
print(f"容器: {c.name}")

# 验证依赖
print("\n1. 验证依赖:")
ret = c.exec_run(["python", "-c", "import matplotlib, pandas, numpy; print('matplotlib', matplotlib.__version__, '| pandas', pandas.__version__)"])
if ret.exit_code == 0:
    print(f"  ✅ {ret.output.decode().strip()}")
else:
    print(f"  ❌ {ret.output.decode().strip()[:200]}")

# 测试生成图表
print("\n2. 测试生成 PNG:")
test_script = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.bar(['A','B','C'], [10, 25, 15])
plt.savefig('/workspace/test.png', dpi=72)
print('OK')
"""
ret = c.exec_run(["python", "-c", test_script])
if ret.exit_code == 0 and "OK" in ret.output.decode():
    print(f"  ✅ 图表生成成功!")
    ret = c.exec_run(["bash", "-c", "ls -lh /workspace/test.png"])
    print(f"  📁 {ret.output.decode().strip()}")
else:
    print(f"  ❌ {ret.output.decode().strip()[:300]}")

client.close()
print("\n=== 完成 ===")
