import docker
from dotenv import load_dotenv

load_dotenv()

client = docker.from_env()
containers = client.containers.list(filters={'name': 'erp-sandbox'})
print(f"当前 {len(containers)} 个沙箱容器:")
for c in containers:
    print(f"  - {c.name}")
    print(f"    镜像: {c.image.tags[0]}")
    
    # 测试能不能写文件和执行
    ret = c.exec_run(["bash", "-c", "echo 'test' > /workspace/test_write.txt && cat /workspace/test_write.txt"])
    print(f"    写文件测试: exit={ret.exit_code}, output={ret.output.decode().strip()}")
    
    # 测试 import matplotlib
    ret = c.exec_run(["python", "-c", "import matplotlib; print('ok')"])
    print(f"    import matplotlib: exit={ret.exit_code}, output={ret.output.decode().strip()[:100]}")
    print()

client.close()
