import sys
import os

# app 폴더를 path에 추가하여 import 가능하도록 함
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.llm_engine import get_parsed_content_from_text, configure_gemini

# 환경변수에서 API 키 로드 (테스트용)
# 터미널에서 export GEMINI_API_KEY="your_key" 후 실행 권장
configure_gemini()

def test_text_parsing():
    sample_text = """
    다음 지문을 읽고 물음에 답하시오.
    
    In 1870 the first all-metal machine appeared. It had a large front wheel and a small back wheel. 
    Hard rubber tires gave people a much better ride. This machine was the first one to be called a bicycle, "two wheels." 
    Though these bicycles were expensive, they were enjoyed by young men.
    
    1. 이 기계의 특징이 아닌 것은?
    (1) 비쌌다. (2) 젊은 남자들이 즐겼다. (3) 1870년에 등장했다.
    """
    
    print("Testing get_parsed_content_from_text...")
    result = get_parsed_content_from_text(sample_text)
    
    print("=== 파싱 결과 ===")
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY 환경변수가 설정되지 않았습니다. 테스트가 실패할 수 있습니다.")
    test_text_parsing()
