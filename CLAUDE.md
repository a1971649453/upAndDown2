# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

upAndDown2 是一个安全的内外网文件传输工具，通过Fernet加密实现"内网上传，外网下载"的跨网络文件传输。项目采用Python + Tkinter/CustomTkinter构建现代化桌面界面。

## 核心架构

### 双端架构
- **云内端（上传端）**: `intranet_gui_client_optimized.py` - 优化版上传客户端，支持文件拖拽和剪切板监听
- **云外端（下载端）**: `external_client.py` - 下载客户端，支持自动轮询和文件解密

### 关键组件层次
```
├── 入口层: intranet_gui_client_optimized.py, external_client.py
├── 业务服务层: services/ (clipboard_service, file_service, smart_assistant)
├── UI组件层: ui/ (modern UI components with CustomTkinter fallback)
├── 核心系统层: core/ (event_system, performance_monitor)
└── 工具层: network_utils.py, config_manager.py
```

### 加密安全架构
- 基于PBKDF2-HMAC-SHA256 + Fernet对称加密
- 密钥通过Windows keyring安全存储，不在配置文件中明文保存
- 支持文件分片上传（默认3MB分片）

## 开发命令

### 环境配置
```bash
# 安装依赖
pip install -r requirements.txt

# 初始化配置（必须）
python config_setup.py
```

### 启动应用
```bash
# 启动云内端（上传）
python intranet_gui_client_optimized.py

# 启动云外端（下载）
python external_client.py
# 或使用批处理脚本
yunwai.bat

# Cookie同步服务（可选）
start_cookie_server.bat
```

### 一键部署
```bash
# 在线环境
一键安装.bat

# 离线环境
下载离线包.bat  # 在有网络环境下载
离线安装.bat    # 在目标离线环境安装
```

## 关键技术特性

### UI现代化适配
- **首选**: CustomTkinter现代化界面
- **降级**: 传统Tkinter + ttkthemes
- **最终降级**: 纯Tkinter
- UI组件统一通过 `ui/components/base_components.py` 封装

### 剪切板监听优化
- 智能间隔调整：0.5-2秒动态间隔
- 混合策略检测：pyperclip + win32clipboard
- 防重复缓存机制

### 性能监控集成
- `core/performance_monitor.py` 提供内存、CPU监控
- 事件系统 (`core/event_system.py`) 实现组件解耦通信
- 智能助手 (`services/smart_assistant.py`) 记录用户偏好

## 配置管理

### 核心配置文件 `config.ini`
```ini
# 服务器配置
upload_url = http://emap.wisedu.com/res/sys/emapcomponent/file/uploadTempFileAsAttachment.do
query_url = http://emap.wisedu.com/res/sys/emapcomponent/file/getUploadedAttachment/fileUploadToken.do

# 文件配置
max_file_size_mb = 6
chunk_size_mb = 3

# 轮询配置
poll_interval_seconds = 10
```

### 配置管理器特性
- 懒加载机制避免主线程I/O阻塞
- 自动BOM检测和处理
- 线程安全的配置更新

## 开发注意事项

### 依赖管理
- CustomTkinter >= 5.2.0（现代UI）
- cryptography >= 45.0.3（加密）
- pywin32 == 310（Windows剪切板）
- tkinterdnd2 >= 0.3.0（拖拽支持）

### 代码约定
- 所有UI组件必须支持CustomTkinter降级到传统Tkinter
- 文件操作使用相对路径，配合 `downloads/` 目录
- 错误处理使用 `@safe_operation` 装饰器统一处理
- 多线程操作必须使用 `queue.Queue` 进行线程间通信

### 安全规范
- 永远不要在代码中硬编码密码或密钥
- 加密密钥必须通过 `keyring` 管理
- 文件上传前必须验证文件大小和类型
- 服务器文件删除操作需要用户确认

### 测试验证
项目当前没有单元测试框架，手动测试重点关注：
1. 内外网环境下的文件传输完整性
2. UI在不同Windows版本的兼容性
3. 长时间运行的内存泄漏检测
4. 加密解密的密钥一致性验证