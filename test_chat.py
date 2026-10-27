"""测试发一个生成图表的请求，看沙箱是否正常"""
import requests
import json

url = "http://localhost:8000/api/chat/stream"

# 模拟一个生成柱状图的请求
payload = {
    "thread_id": "test-sandbox-002",
    "user_id": "user-001",
    "message": "帮我生成一个柱状图，数据是：产品A销量100，产品B销量200，产品C销量150",
}

print("发送测试请求...")
try:
    resp = requests.post(url, json=payload, stream=True, timeout=30)
    print(f"状态码: {resp.status_code}")
    
    # 读前几行 SSE 数据
    for i, line in enumerate(resp.iter_lines()):
        if i > 20:
            break
        if line:
            line_str = line.decode('utf-8')
            print(line_str[:200])
except Exception as e:
    print(f"请求失败: {e}")
