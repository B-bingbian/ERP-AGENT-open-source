import docker
import json
from dotenv import load_dotenv

load_dotenv()

client = docker.from_env()
c = client.containers.list(filters={'name': 'erp-sandbox-warm'})[0]
print(f"容器: {c.name}")

# 直接写一个完整的测试脚本到容器里，然后执行
test_script = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import sys

# 写参数
params = {
    "chart_type": "bar",
    "data": [{"label": "A", "value": 10}, {"label": "B", "value": 20}],
    "title": "Test",
    "output_path": "/workspace/charts/test.png",
}

# 生成图表
fig, ax = plt.subplots()
ax.bar([d['label'] for d in params['data']], [d['value'] for d in params['data']])
plt.savefig(params['output_path'])
print('OK: chart saved to', params['output_path'])
"""

# 写到容器里
import tarfile
import io

# 用 put_archive 上传脚本
tar_buf = io.BytesIO()
with tarfile.open(fileobj=tar_buf, mode='w') as tar:
    data = test_script.encode('utf-8')
    info = tarfile.TarInfo(name='test_chart.py')
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))
tar_buf.seek(0)

c.put_archive("/workspace", tar_buf)
print("脚本已上传")

# 执行
ret = c.exec_run(["python", "/workspace/test_chart.py"])
print(f"exit={ret.exit_code}")
print(f"输出: {ret.output.decode().strip()[:500]}")

client.close()
