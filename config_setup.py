# config_setup.py (v3.0 - 使用keyring安全存储密码)

import configparser
import os
import keyring  # NEW
import getpass  # NEW: for securely getting password from terminal

def create_config():
    config = configparser.ConfigParser()
    
    print("--- 云剪切板工具：首次配置向导 (安全版) ---")
    print("这将创建一个 config.ini 文件来存储您的URL配置。")
    print("您的密钥（密码）将被安全地存储在操作系统的凭据管理器中。")
    
    while True:
        # NEW: Use getpass to hide password input
        password = getpass.getpass("请输入您用于加密和解密的密钥（密码），请确保两台电脑设置相同: ")
        if len(password) >= 12:
            break
        print("错误：密码长度至少需要12位，以确保安全。")
    
    # NEW: Store password securely
    try:
        keyring.set_password("cloud_clipboard_service", "secret_key", password)
        print("\n✅ 密钥已成功保存到系统凭据管理器中。")
    except Exception as e:
        print(f"\n❌ 无法保存密钥到系统凭据管理器: {e}")
        print("请确保您已安装 'keyring' 库。")
        input("\n按回车键退出。")
        return

    # MODIFIED: Removed 'SECRET_PASSWORD' from config file
    config['DEFAULT'] = {
        'COOKIE': '请在浏览器登录后，等待油猴脚本自动更新此项',
        'UPLOAD_URL': 'http://emap.wisedu.com/res/sys/emapcomponent/file/uploadTempFileAsAttachment.do',
        'QUERY_URL': 'http://emap.wisedu.com/res/sys/emapcomponent/file/getUploadedAttachment/fileUploadToken.do',
        'BASE_DOWNLOAD_URL': 'http://emap.wisedu.com',
        'DELETE_URL_TEMPLATE': 'http://emap.wisedu.com/res/sys/emapcomponent/file/deleteFileByWid/{file_id}.do',
        'DOWNLOAD_DIR': './downloads/',
        'POLL_INTERVAL_SECONDS': '10',
        'MAX_FILE_SIZE_MB': '6',  # 上传大小上限
        'CHUNK_SIZE_MB': '3'  # 新增：定义分片大小，应略小于上限

    }
    
    with open('config.ini', 'w', encoding='utf-8') as configfile:
        config.write(configfile)
        
    print("\n✅ 配置文件 'config.ini' 创建成功！")
    print("所有URL和基础配置已保存。")

if __name__ == '__main__':
    if os.path.exists('config.ini'):
        print("'config.ini' 文件已存在。如果您想重新配置，请先删除它，然后重新运行此脚本。")
    else:
        create_config()
    input("\n按回车键退出。")