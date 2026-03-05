import requests
import json
import time

# 替换为你实际的本地后端服务地址和用户鉴权 Token
BASE_URL = "http://127.0.0.1:5000"
USER_TOKEN = "" # 如果你的系统需要 Token，填写在这里

def submit_task():
    print("1. Submitting Task...")
    url = f"{BASE_URL}/api/v1/tasks/submit"
    
    headers = {
        "Content-Type": "application/json"
    }
    if USER_TOKEN:
        headers["Authorization"] = f"Bearer {USER_TOKEN}"
        
    payload = {
        "model": "workflow-earing-ad",
        "prompt": "Test Product Info", 
        "input_file_url": [
            "https://pub-826107e0701d495a8c5318616ce8ac43.r2.dev/uploads/user_1/2026/03/05/63c42b95-20260305112404_9258_51.jpg"
        ],
        "params": {}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        print(f"Submit Source Response: {data}")
        
        # 假设返回的数据结构是 {"data": {"task_id": "..."}} (请根据实际情况调整)
        task_id = data.get("data", {}).get("task_id") or data.get("task_id")
        if not task_id:
            print("Failed to get task_id from response")
            return None
            
        print(f"Task submitted successfully! Task ID: {task_id}")
        return task_id
        
    except Exception as e:
        print(f"Submission failed: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"Response text: {response.text}")
        return None

def poll_task_status(task_id):
    print("\n2. Polling Task Status...")
    url = f"{BASE_URL}/api/v1/tasks/{task_id}/status" # 请确认这个 URL 是你查询状态的正确路由
    
    headers = {}
    if USER_TOKEN:
        headers["Authorization"] = f"Bearer {USER_TOKEN}"
        
    max_retries = 300 # 最多等十分钟
    for i in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # 这里假设后台返回 {"data": {"status": "processing", "progress": 50, ...}}
            task_info = data.get("data", data)
            status = task_info.get("status")
            progress = task_info.get("progress", 0)
            
            print(f"[{i}] Status: {status}, Progress: {progress}%")
            
            if status == "success":
                result_url = task_info.get("result_url")
                print(f"\n✅ Task completed successfully! Result URL:\n{result_url}")
                break
            elif status == "failed" or status == "cancelled":
                fail_reason = task_info.get("fail_reason", "Unknown error")
                print(f"\n❌ Task failed! Reason:\n{fail_reason}")
                break
                
        except Exception as e:
            print(f"Status check failed: {e}")
            
        time.sleep(2) # 每 2 秒轮询一次

if __name__ == "__main__":
    task_id = submit_task()
    if task_id:
        poll_task_status(task_id)
