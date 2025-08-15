#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件修复工具
修复 config.ini 文件中的BOM和格式问题

使用方法：
python fix_config.py
"""

import os
import configparser
import shutil
from datetime import datetime

def check_and_fix_config(config_file='config.ini'):
    """检查并修复配置文件"""
    print(f"🔍 检查配置文件: {config_file}")
    
    if not os.path.exists(config_file):
        print(f"❌ 配置文件 {config_file} 不存在")
        return False
    
    try:
        # 读取文件内容
        with open(config_file, 'rb') as f:
            content = f.read()
        
        print(f"📊 文件大小: {len(content)} 字节")
        
        # 检查BOM
        has_bom = content.startswith(b'\xef\xbb\xbf')
        if has_bom:
            print("⚠️ 检测到BOM字符，正在修复...")
            
            # 创建备份
            backup_file = f"{config_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(config_file, backup_file)
            print(f"📋 已创建备份: {backup_file}")
            
            # 移除BOM
            content_without_bom = content[3:]
            with open(config_file, 'wb') as f:
                f.write(content_without_bom)
            
            print("✅ BOM已移除")
        else:
            print("✅ 未检测到BOM字符")
        
        # 尝试解析配置文件
        config = configparser.ConfigParser(interpolation=None)
        config.read(config_file, encoding='utf-8')
        
        if 'DEFAULT' in config:
            print("✅ 配置文件格式正确")
            
            # 显示配置内容
            print("\n📋 当前配置内容:")
            for key, value in config['DEFAULT'].items():
                if key == 'COOKIE':
                    # 隐藏Cookie值，只显示长度
                    print(f"  {key}: [长度: {len(value)} 字符]")
                else:
                    print(f"  {key}: {value}")
            
            return True
        else:
            print("❌ 配置文件缺少DEFAULT节")
            return False
            
    except Exception as e:
        print(f"❌ 配置文件检查失败: {e}")
        return False

def create_clean_config(config_file='config.ini'):
    """创建干净的配置文件"""
    print(f"\n🔧 创建干净的配置文件: {config_file}")
    
    try:
        # 创建备份
        if os.path.exists(config_file):
            backup_file = f"{config_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(config_file, backup_file)
            print(f"📋 已创建备份: {backup_file}")
        
        # 创建新的配置文件
        config = configparser.ConfigParser(interpolation=None)
        config['DEFAULT'] = {
            'COOKIE': '',
            'UPLOAD_URL': 'http://your-server.com/upload',
            'QUERY_URL': 'http://your-server.com/query',
            'BASE_DOWNLOAD_URL': 'http://your-server.com',
            'DELETE_URL_TEMPLATE': 'http://your-server.com/delete/{file_id}',
            'DOWNLOAD_DIR': './downloads/',
            'BASE_POLL_INTERVAL': '5',
            'MAX_POLL_INTERVAL': '60',
            'POLL_INCREASE_FACTOR': '1.5',
            'AUTO_STOP_MINUTES': '10',
            'MAX_FILE_SIZE_MB': '6',
            'CHUNK_SIZE_MB': '3'
        }
        
        # 写入配置文件，确保不产生BOM
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)
        
        print("✅ 干净的配置文件已创建")
        return True
        
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 配置文件修复工具")
    print("=" * 50)
    
    # 检查当前配置文件
    if check_and_fix_config():
        print("\n🎉 配置文件检查完成，无需修复")
    else:
        print("\n⚠️ 配置文件存在问题，尝试修复...")
        
        # 尝试修复
        if check_and_fix_config():
            print("\n🎉 配置文件修复成功")
        else:
            print("\n🔧 尝试创建干净的配置文件...")
            
            if create_clean_config():
                print("\n🎉 干净的配置文件创建成功")
                print("💡 请重新运行配置向导设置服务器地址和密钥")
            else:
                print("\n❌ 配置文件修复失败")
                print("💡 请手动检查配置文件或联系技术支持")
    
    print("\n" + "=" * 50)
    print("修复完成！")

if __name__ == "__main__":
    main()
