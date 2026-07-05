import subprocess
import sys

def run_app():
    print("[EduAI] 스마트 학습 플랫폼(Streamlit)을 시작합니다...")
    print("브라우저 창이 자동으로 열립니다.")
    print("-------------------------------------------------")
    # Streamlit은 실행 시 자동으로 브라우저 창을 띄워줍니다.
    subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])

if __name__ == "__main__":
    run_app()
