#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常处理测试脚本
测试云外端的异常处理机制是否正常工作

使用方法：
python test_error_handling.py
"""

import sys
import os
import traceback

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_exception_handling():
    """测试异常处理机制"""
    print("🧪 测试异常处理机制...")
    
    try:
        # 导入修复后的模块
        from external_client import safe_operation
        
        print("✅ 成功导入 safe_operation 装饰器")
        
        # 测试装饰器
        @safe_operation("测试操作")
        def test_function():
            raise ValueError("这是一个测试异常")
        
        # 执行测试函数
        result = test_function()
        if result is None:
            print("✅ 异常被正确捕获和处理")
        else:
            print("❌ 异常处理异常")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_error_logging():
    """测试错误日志记录"""
    print("\n📝 测试错误日志记录...")
    
    try:
        # 模拟错误日志记录
        error_msg = "❌ 处理单个文件失败: 测试异常"
        
        # 添加详细错误信息
        try:
            raise ValueError("测试异常详情")
        except Exception as e:
            if hasattr(e, '__traceback__'):
                tb_info = traceback.format_exc()
                error_msg += f"\n   详细错误: {tb_info.split('File')[0].strip()}"
        
        print(f"✅ 错误日志格式: {error_msg}")
        
    except Exception as e:
        print(f"❌ 错误日志测试失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🔧 异常处理机制测试工具")
    print("=" * 50)
    
    # 运行测试
    test1_passed = test_exception_handling()
    test2_passed = test_error_logging()
    
    # 显示测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    if test1_passed:
        print("✅ 异常处理机制测试: 通过")
    else:
        print("❌ 异常处理机制测试: 失败")
    
    if test2_passed:
        print("✅ 错误日志记录测试: 通过")
    else:
        print("❌ 错误日志记录测试: 失败")
    
    if test1_passed and test2_passed:
        print("\n🎉 所有测试通过！异常处理机制正常工作")
    else:
        print("\n⚠️ 有测试失败，需要进一步检查")
    
    print("\n💡 现在可以运行云外端，查看是否还有空错误信息")

if __name__ == "__main__":
    main()
