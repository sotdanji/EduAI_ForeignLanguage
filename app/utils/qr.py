import socket
import qrcode
from PIL import Image

def get_local_ip() -> str:
    """내부 네트워크의 로컬 IPv4 주소를 반환합니다."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 10.255.255.255는 연결 대상이 아니며 IP 라우팅을 확인하기 위한 더미 IP입니다.
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def generate_qr_code(data: str) -> Image.Image:
    """주어진 문자열(URL 등)로 QR 코드 이미지를 생성합니다."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img
