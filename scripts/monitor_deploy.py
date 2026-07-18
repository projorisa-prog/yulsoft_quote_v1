import os
import sys
import time
import subprocess
import requests
import httpx
from openai import OpenAI

# 환경변수 로드
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
SERVICE_ID = os.getenv("RENDER_SERVICE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not RENDER_API_KEY or not SERVICE_ID:
    print("❌ 에러: RENDER_API_KEY 또는 RENDER_SERVICE_ID 설정이 누락되었습니다.")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

def check_deployment_status():
    """Render API를 호출하여 최신 배포 상태를 조회합니다."""
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            deploys = response.json()
            if deploys:
                # 가장 최근 배포 건 정보 가져오기
                latest = deploys[0]['deploy']
                return latest['status'], latest['id']
    except Exception as e:
        print(f"API 호출 중 오류 발생: {e}")
    return "unknown", None

def get_error_logs(deploy_id):
    """실패한 배포의 빌드/런타임 로그를 수집합니다."""
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{deploy_id}/logs"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            # 로그 데이터를 텍스트 형태로 결합
            log_data = response.json()
            logs = [item.get('text', '') for item in log_data]
            return "\n".join(logs[-100:])  # 최근 100줄만 추출
    except Exception as e:
        print(f"로그 수집 중 오류 발생: {e}")
    return ""

def ask_ai_agent_to_fix(error_logs):
    """네모트론(Nemotron) API를 사용하여 에러 원인을 분석하고 코드를 수정합니다."""
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY") 
    
    if not NVIDIA_API_KEY:
        print("⚠️ NVIDIA_API_KEY가 없어 자가 치유를 진행할 수 없습니다.")
        return None

    # 🔧 프록시 충돌을 방지하기 위해 httpx 클라이언트를 직접 생성하여 주입합니다.
    http_client = httpx.Client(proxies={})

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=NVIDIA_API_KEY,
        http_client=http_client  # 💡 충돌 방지용 클라이언트 주입
    )
    
    prompt = f"""
    당신은 율소프트 개발 팀의 '자가 치유 디버깅 에이전트'입니다.
    현재 FastAPI 백엔드를 Render에 배포하는 도중 에러가 발생하여 배포가 실패했습니다.
    
    [최근 배포 에러 로그]
    {error_logs}
    
    [요구 사항]
    1. 이 에러를 발생시킨 원인을 분석하세요.
    2. 이를 해결하기 위해 프로젝트 내 어떤 파일(`app/main.py` 또는 `requirements.txt` 등)을 어떻게 수정해야 하는지 알려주세요.
    3. 반드시 파이썬 코드가 직접 읽어서 파싱할 수 있도록 아래 형식을 엄격히 지켜 응답해주세요. 다른 부연 설명 없이 형식만 맞춰서 출력해야 합니다.
    
    [응답 형식]
    FILE: 파일경로
    CODE:
    수정된 전체 파일 코드 내용
    """
    
    try:
        # 모델명은 네모트론을 호출하도록 유지합니다.
        response = client.chat.completions.create(
            model="nvidia/llama-3.1-nemotron-70b-instruct", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"네모트론 모델 호출 실패: {e}")
        return None

def apply_patch(ai_response):
    """AI가 준 솔루션을 분석하여 로컬 파일을 덮어씁니다."""
    if not ai_response or "FILE:" not in ai_response or "CODE:" not in ai_response:
        print("⚠️ AI 응답 형식이 올바르지 않아 수정을 건너뜁니다.")
        return False
        
    try:
        parts = ai_response.split("CODE:")
        file_part = parts[0].replace("FILE:", "").strip()
        code_part = parts[1].strip()
        
        # 파일 수정 적용
        with open(file_part, "w", encoding="utf-8") as f:
            f.write(code_part)
        print(f"🔧 에이전트가 [{file_part}] 파일을 자동으로 수정했습니다.")
        return True
    except Exception as e:
        print(f"파일 패치 적용 실패: {e}")
        return False

def push_changes():
    """수정된 코드를 GitHub Actions 환경에서 원격 저장소로 자동 Push합니다."""
    try:
        # Git 유저 설정 (Actions 봇 계정명)
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
        subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
        
        # 스테이징 및 커밋
        subprocess.run(["git", "add", "."], check=True)
        # 이미 수정본이 변경사항을 만들었는지 확인 후 커밋
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip() == "":
            subprocess.run(["git", "commit", "-m", "fix: AI auto repair deployment error"], check=True)
            # 재귀 배포를 위한 Push
            subprocess.run(["git", "push"], check=True)
            print("🚀 수정된 코드가 GitHub에 정상적으로 push되었습니다. Render가 재배포를 시작합니다.")
            return True
    except Exception as e:
        print(f"Git Push 실패: {e}")
    return False

# 메인 실행 루프
print("🕵️ 배포 모니터링 에이전트 가동 시작...")
check_count = 0

while check_count < 20:  # 최대 10분 동안 관측 (30초 * 20)
    status, deploy_id = check_deployment_status()
    print(f"현재 Render 배포 상태: [{status}] (체크 {check_count+1}/20)")
    
    if status == "live":
        print("🎉 축하합니다! 배포가 성공적으로 완료되어 서비스가 Live 상태입니다.")
        sys.exit(0)
    elif status in ["failed", "deactivated", "build_failed"]:
        print("❌ 배포 실패 감지! 자가 치유(Self-Healing) 프로세스를 가동합니다.")
        logs = get_error_logs(deploy_id)
        ai_solution = ask_ai_agent_to_fix(logs)
        
        if ai_solution:
            success = apply_patch(ai_solution)
            if success:
                push_changes()
        sys.exit(0) # 에이전트 임무 완료 후 워크플로우 종료 (새 push가 새 워크플로우 작동시킴)
        
    check_count += 1
    time.sleep(30)

print("⏳ 배포 모니터링 타임아웃 (배포가 너무 오래 걸립니다.)")