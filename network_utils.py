# network_utils.py

import json
import base64
import os
import requests
import io

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from requests_toolbelt.multipart.encoder import MultipartEncoder

# --- 加密/解密核心函数 ---

def get_encryption_key(password, salt=b'salt_for_bmad_clipboard'):
    """根据密码派生一个安全的加密密钥。"""
    if not isinstance(password, bytes):
        password = password.encode('utf-8')
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000, backend=default_backend())
    return base64.urlsafe_b64encode(kdf.derive(password))

def create_and_encrypt_payload(file_path, password, is_from_text=False):
    """创建并加密文件载荷。"""
    key = get_encryption_key(password)
    f = Fernet(key)
    original_filename = os.path.basename(file_path)
    with open(file_path, 'rb') as file_handle:
        file_content = file_handle.read()
    content_base64 = base64.b64encode(file_content).decode('utf-8')
    payload = {"filename": original_filename, "content_base64": content_base64, "is_from_text": is_from_text}
    return f.encrypt(json.dumps(payload).encode('utf-8'))

def decrypt_and_parse_payload(encrypted_data, password):
    """解密并解析载荷。"""
    key = get_encryption_key(password)
    f = Fernet(key)
    decrypted_bytes = f.decrypt(encrypted_data)
    payload = json.loads(decrypted_bytes.decode('utf-8'))
    return payload

# --- 网络操作函数 ---

def upload_data(encrypted_payload_bytes, config, status_queue, custom_filename=None):
    """
    修改：使用 requests-toolbelt 实现流式上传，减少内存占用。
    """
    try:
        upload_filename = custom_filename if custom_filename else f"clipboard_payload_{base64.urlsafe_b64encode(os.urandom(6)).decode()}.encrypted"

        # 使用 MultipartEncoder 创建一个可流式处理的请求体
        m = MultipartEncoder(
            fields={
                'scope': 'fileUploadToke',
                'fileToken': 'fileUploadToken',
                'storeId': 'file',
                'isSingle': '0',
                # 将加密后的字节流包装成一个内存中的文件对象来上传
                'bhFile': (upload_filename, io.BytesIO(encrypted_payload_bytes), 'application/octet-stream')
            }
        )

        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Cookie': config['DEFAULT']['COOKIE'],
            'User-Agent': 'Mozilla/5.0',
            # 关键：设置正确的 Content-Type，其值由 MultipartEncoder 生成
            'Content-Type': m.content_type
        }

        status_queue.put(('info', f"正在流式上传: {os.path.basename(upload_filename)}..."))
        upload_url = config['DEFAULT']['UPLOAD_URL']

        # 直接将 MultipartEncoder 对象作为 data 参数传入
        response = requests.post(upload_url, data=m, headers=headers, timeout=300)
        response.raise_for_status()

        if response.json().get("success"):
            status_queue.put(('success', f"上传成功: {os.path.basename(upload_filename)}"))
            return True
        else:
            status_queue.put(('error', f"上传失败: {response.json()}"))
            return False
    except Exception as e:
        status_queue.put(('error', f"上传出错: {e}"))
    return False


def delete_server_file(file_id, config, status_queue):
    """从服务器删除文件。"""
    delete_url = config['DEFAULT']['DELETE_URL_TEMPLATE'].format(file_id=file_id)
    headers = {'Cookie': config['DEFAULT']['COOKIE'], 'User-Agent': 'Mozilla/5.0'}
    status_queue.put(('info', f"正在删除服务器文件 (ID: {file_id})"))
    try:
        response = requests.post(delete_url, headers=headers, timeout=30)
        response.raise_for_status()
        response_json = response.json()
        if response_json.get("success") and response_json.get("count", 0) > 0:
            status_queue.put(('success', f"服务器文件 (ID: {file_id}) 删除成功。"))
        else:
            status_queue.put(('warning', f"删除请求已发送，但服务器未报告成功删除。"))
    except Exception as e:
        status_queue.put(('error', f"调用删除API时出错: {e}"))