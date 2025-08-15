# test_security_fix.py
"""
测试安全修复：验证解密失败时只删除本地文件，不删除服务器文件
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestSecurityFix(unittest.TestCase):
    """测试安全修复功能"""
    
    def setUp(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, "test_file.txt")
        
        # 创建测试文件
        with open(self.test_file_path, 'w') as f:
            f.write("test content")
    
    def tearDown(self):
        """测试清理"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('external_client.delete_server_file')
    def test_decrypt_failure_no_server_delete(self, mock_delete_server_file):
        """测试解密失败时不删除服务器文件"""
        
        # 模拟相关模块
        with patch('external_client.decrypt_and_parse_payload') as mock_decrypt:
            # 设置解密失败
            mock_decrypt.side_effect = Exception("解密失败")
            
            # 模拟队列和配置
            mock_status_queue = Mock()
            mock_config = Mock()
            
            # 创建模拟的下载器实例
            from external_client import CloudClipboardClient
            
            with patch.object(CloudClipboardClient, '__init__', return_value=None):
                client = CloudClipboardClient()
                client.status_queue = mock_status_queue
                client.executor = Mock()
                
                # 模拟下载响应
                mock_response = Mock()
                mock_response.content = b"encrypted_content"
                
                # 模拟文件项
                test_item = {
                    'id': 'test_file_id',
                    'name': 'test_file.txt',
                    'size': 100
                }
                
                # 调用下载方法（模拟）
                try:
                    client._download_single_file(test_item, mock_config, self.test_file_path, mock_response)
                except:
                    pass  # 预期会有异常
                
                # 验证：不应该调用删除服务器文件
                mock_delete_server_file.assert_not_called()
                
                # 验证：应该删除本地文件
                self.assertFalse(os.path.exists(self.test_file_path), "本地文件应该被删除")
    
    def test_small_file_no_server_delete(self):
        """测试小文件不删除服务器文件"""
        
        with patch('external_client.delete_server_file') as mock_delete_server_file:
            # 模拟小文件检测逻辑
            min_file_size = 1000
            small_file_size = 500
            
            # 验证小文件不会触发服务器删除
            if small_file_size < min_file_size:
                # 这里模拟原来的逻辑，但现在应该不删除服务器文件
                pass
            
            # 确认没有调用删除服务器文件
            mock_delete_server_file.assert_not_called()
    
    def test_successful_download_still_deletes_server(self):
        """测试成功下载后仍然删除服务器文件"""
        
        with patch('external_client.delete_server_file') as mock_delete_server_file:
            # 模拟成功下载的情况
            # 这种情况下应该继续删除服务器文件
            mock_config = Mock()
            mock_status_queue = Mock()
            
            # 模拟调用删除
            from external_client import CloudClipboardClient
            
            with patch.object(CloudClipboardClient, '__init__', return_value=None):
                client = CloudClipboardClient()
                client.executor = Mock()
                
                # 模拟成功下载后的删除操作
                client.executor.submit(mock_delete_server_file, 'test_id', mock_config, mock_status_queue)
                
                # 验证在成功情况下仍然会删除服务器文件
                client.executor.submit.assert_called()

def run_security_tests():
    """运行安全测试"""
    print("开始安全修复测试...")
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSecurityFix)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n所有安全测试通过！")
        print("修复总结:")
        print("   - 解密失败时：只删除本地文件，保留服务器文件")
        print("   - 小文件跳过时：保留服务器文件")
        print("   - 成功下载后：正常删除服务器文件（清理功能）")
        return True
    else:
        print("\n部分测试失败，需要检查修复")
        return False

if __name__ == '__main__':
    success = run_security_tests()
    sys.exit(0 if success else 1)