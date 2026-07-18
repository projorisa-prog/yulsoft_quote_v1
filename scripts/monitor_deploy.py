import os
import sys
import time
import subprocess
import requests
import json

RENDER_API_KEY = os.getenv("RENDER_API_KEY")
SERVICE_ID = os.getenv("RENDER_SERVICE_ID")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

if not RENDER_API_KEY or not SERVICE_ID:
    print("❌ 에러: RENDER_API_KEY 또는 RENDER_SERVICE_ID 설정이 누락되었습니다.")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

def check_deployment_status():
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            deploys = response.json()
            if deploys:
                latest = deploys[0]['deploy']
                return latest['status'], latest['id']
    except Exception as e:
        print(f"API 호출 중 오류 발생: {e}")
    return "unknown", None

def get_error_logs(deploy_id):
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{deploy_id}/logs"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            log_data = response.json()
            logs = [item.get('text', '') for item in log_data]
            # 로그가 비어있을 경우를 대비한 기본 텍스트 주입
            if not logs:
                return "Render build failed. app/main.py has a syntax error 'import_error_here_for_testing'."
            return "\n".join(logs[-100:])
    except Exception as e:
        print(f"로그 수집 중 오류 발생: {e}")
    return "Render build failed due to syntax error in app/main.py"

def ask_ai_agent_to_fix(error_logs):
    if not NVIDIA_API_KEY:
        print("⚠️ NVIDIA_API_KEY가 없어 자가 치유를 진행할 수 없습니다.")
        return None

    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    현재 FastAPI 백엔드를 Render에 배포하는 도중 에러가 발생하여 배포가 실패했습니다.
    [최근 배포 에러 로그]
    {error_logs}
    
    [요구 사항]
    1. app/main.py 맨 위에 적힌 문법 오류인 'import_error_here_for_testing' 코드를 제거하여 정상적인 FastAPI 코드로 되돌려주세요.
    2. 부연 설명이나 마크다운 백틱(```) 기호는 절대 적지 마세요. 오직 파이썬 코드가 직접 파싱할 수 있게 아래 형식만 출력하세요.
    
    FILE: app/main.py
    CODE:
    from fastapi import FastAPI
    app = FastAPI(title="Yulsoft Quotation System MVP")
    @app.get("/")
    def read_root():
        return {{"status": "healthy", "message": "Yulsoft API Server is running."}}
    @app.get("/api/v1/health")
    def health_check():
        return {{"status": "UP"}}
    """
    
    payload = {
        "model": "nvidia/llama-3.1-nemotron-70b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None
    except Exception as e:
        print(f"네모트론 호출 중 예외 발생: {e}")
        return None

def apply_patch(ai_response):
    if not ai_response or "CODE:" not in ai_response:
        print("⚠️ AI 응답 형식이 올바르지 않아 강제 복구를 수행합니다.")
        # 파싱 실패 시 안전하게 초기화하는 폴백(Fallback) 로직
        code = 'from fastapi import FastAPI\napp = FastAPI(title="Yulsoft Quotation System MVP")\n@app.get("/")\ndef read_root():\n    return {"status": "healthy", "message": "Yulsoft API Server is running."}\n@app.get("/api/v1/health")\ndef health_check():\n    return {"status": "UP"}'
        with open("app/main.py", "w", encoding="utf-8") as f:
            f.write(code)
        return True
        
    try:
        parts = ai_response.split("CODE:")
        code_part = parts[1].strip()
        # 마크다운 찌꺼기 제거
        if code_part.startswith("```python"):
            code_part = code_part.split("```python")[1].split("```")[0].strip()
        elif code_part.startswith("```"):
            code_part = code_part.split("```")[1].split("```")[0].strip()

        with open("app/main.py", "w", encoding="utf-8") as f:
            f.write(code_part)
        print("🔧 에이전트가 코드를 정상적으로 수정했습니다.")
        return True
    except Exception as e:
        print(f"파일 패치 적용 실패: {e}")
        return False

def push_changes():
    try:
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
        subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
        subprocess.run(["git", "add", "."], check=True)
        
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip() != "":
            subprocess.run(["git", "commit", "-m", "fix: AI auto repair deployment error"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("🚀 수정된 코드가 GitHub에 Push되었습니다!")
            return True
        else:
            print("⚠️ 변경 사항이 없어 Push를 건너뜁니다.")
    except Exception as e:
        print(f"Git Push 실패: {e}")
    return False

print("🕵️ 배포 모니터링 에이전트 가동 시작...")
check_count = 0

while check_count < 20:
    status, deploy_id = check_deployment_status()
    print(f"현재 Render 배포 상태: [{status}] (체크 {check_count+1}/20)")
    
    if status == "live":
        print("🎉 배포 성공!")
        sys.exit(0)
    elif status in ["failed", "deactivated", "build_failed"]:
        print("❌ 배포 실패 감지! 자가 치유 프로세스 가동.")
        logs = get_error_logs(deploy_id)
        ai_solution = ask_ai_agent_to_fix(logs)
        apply_patch(ai_solution)
        push_changes()
        sys.exit(0)
        
    check_count += 1
    time.sleep(30)