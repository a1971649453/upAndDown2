# verify_security_fix.py
"""
验证安全修复：检查代码中是否正确移除了解密失败时删除服务器文件的逻辑
"""

import os
import re

def check_security_fix():
    """检查安全修复状态"""
    print("=== 安全修复验证报告 ===")
    
    external_client_path = "external_client.py"
    
    if not os.path.exists(external_client_path):
        print("错误：找不到external_client.py文件")
        return False
    
    with open(external_client_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查修复点
    fixes_found = 0
    issues_found = 0
    
    print("\n1. 检查解密失败处理...")
    
    # 检查解密失败时的处理
    decrypt_error_pattern = r'except.*decrypt_error.*?return'
    decrypt_matches = re.findall(decrypt_error_pattern, content, re.DOTALL)
    
    for match in decrypt_matches:
        if 'delete_server_file' in match:
            print("   ❌ 发现解密失败时仍删除服务器文件")
            issues_found += 1
        elif '只删除本地' in match or '保留.*服务器' in match:
            print("   ✅ 发现正确的安全修复：只删除本地文件")
            fixes_found += 1
    
    print("\n2. 检查小文件处理...")
    
    # 检查小文件处理
    small_file_pattern = r'if.*min_file_size.*?return'
    small_file_matches = re.findall(small_file_pattern, content, re.DOTALL)
    
    for match in small_file_matches:
        if 'delete_server_file' in match:
            print("   ❌ 发现小文件时仍删除服务器文件")
            issues_found += 1
        elif '保留.*服务器' in match:
            print("   ✅ 发现正确的安全修复：保留服务器小文件")
            fixes_found += 1
    
    print("\n3. 检查成功下载后的清理...")
    
    # 检查成功下载后的删除（这个应该保留）
    success_delete_count = content.count('# 异步删除服务器文件')
    if success_delete_count > 0:
        print(f"   ✅ 发现 {success_delete_count} 处成功下载后的服务器清理（应保留）")
    
    print(f"\n=== 验证结果 ===")
    print(f"✅ 发现安全修复: {fixes_found} 处")
    print(f"❌ 发现安全问题: {issues_found} 处")
    
    if issues_found == 0 and fixes_found >= 2:
        print("\n🎉 安全修复验证通过！")
        print("修复摘要:")
        print("   - 解密失败时：只删除本地文件，不删除服务器文件")
        print("   - 小文件跳过时：保留服务器文件")
        print("   - 成功下载后：继续清理服务器文件（正常流程）")
        return True
    else:
        print("\n⚠️ 安全修复可能不完整，请检查代码")
        return False

if __name__ == '__main__':
    check_security_fix()