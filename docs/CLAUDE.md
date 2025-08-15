# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

upAndDown2 是一个安全的文件传输工具，支持内网上传和外网下载。该项目采用客户端-服务器架构，通过加密文件传输实现安全的数据交换。

### 核心组件
- **云外端 (external_client.py)**: 下载端应用，已升级到 v5.9 现代化版本
- **云内端现代化版 (modern_intranet_client.py)**: 新的 v5.0 MVP架构现代化版本 ✅已完成
- **云内端传统版 (intranet_gui_client.py)**: 传统 v4.0 版本，作为兼容性fallback
- **网络工具 (network_utils.py)**: 加密/解密和网络操作核心功能
- **配置管理 (config_manager.py)**: 配置文件读写和Cookie服务器

## 开发环境配置

### 安装依赖
```bash
pip install -r requirements.txt
```

### 首次配置
```bash
python config_setup.py
```
这将安全地将加密密钥存储到系统凭据管理器中。

### 启动应用
```bash
# 云外端 (下载端) - 已现代化
yunwai.bat

# 云内端现代化版 (上传端) - 推荐使用
start_modern_intranet.bat

# 云内端传统版 (兼容性fallback)
启动上传工具.bat

# Cookie同步服务器
start_cookie_server.bat
```

## 技术架构

### 技术栈
- **编程语言**: Python 3.8+
- **UI框架**: 
  - 云外端: CustomTkinter (现代化) + Tkinter (兼容)
  - 云内端: CustomTkinter (现代化MVP架构) + Tkinter (传统兼容版)
- **网络通信**: requests + requests-toolbelt
- **加密**: cryptography (Fernet对称加密)
- **凭证管理**: keyring
- **异步处理**: ThreadPoolExecutor + asyncio
- **拖拽支持**: tkinterdnd2
- **系统监控**: psutil

### 核心配置 (config.ini)
- **智能轮询**: 自适应轮询间隔，避免服务器过载
- **文件大小限制**: 默认6MB，可配置
- **分片上传**: 支持大文件分片传输

## 代码架构模式

### 关键设计原则
1. **UI与业务逻辑分离**: 逐步从耦合架构向分层架构演进
2. **流式处理**: 大文件采用流式哈希和上传，避免内存溢出
3. **异步优先**: 网络和文件操作使用异步模式，防止UI冻结
4. **智能轮询**: 动态调整轮询间隔，平衡性能和资源消耗

### 目录结构
```
upAndDown2/
├── external_client.py      # 云外端主程序 (v5.9) ✅已现代化
├── modern_intranet_client.py # 云内端现代化主程序 (v5.0) ✅已完成
├── intranet_gui_client.py  # 云内端传统版 (v4.0) 兼容性fallback
├── network_utils.py        # 网络工具和加密功能
├── config_manager.py       # 配置管理和Cookie服务
├── config_setup.py         # 首次配置向导
├── config.ini              # 运行时配置文件
├── requirements.txt        # Python依赖清单
├── ui/                     # 现代化UI架构 (MVP模式)
│   ├── main_window.py      # 主窗口框架
│   ├── views/              # 视图层
│   ├── controllers/        # 控制器层
│   ├── components/         # UI组件库
│   ├── layouts/            # 响应式布局
│   └── themes/             # 主题管理
├── services/               # 业务服务层
│   ├── file_service.py     # 文件上传服务
│   ├── clipboard_service.py # 剪切板服务
│   └── smart_assistant.py  # 智能助手
├── core/                   # 核心系统
│   ├── event_system.py     # 事件系统
│   └── performance_monitor.py # 性能监控
├── downloads/              # 下载文件存储目录
│   └── temp_chunks/        # 分片临时文件目录
├── yunwai.bat             # 云外端启动脚本
├── start_modern_intranet.bat # 现代化云内端启动脚本
├── 启动上传工具.bat        # 传统云内端启动脚本
└── start_cookie_server.bat # Cookie服务启动脚本
```

## 开发指南

### 常见开发任务

#### 现代化版本开发 (推荐)
- 基于 modern_intranet_client.py 的 MVP 架构进行开发
- UI组件位于 ui/ 目录，业务逻辑位于 services/ 目录
- 使用事件系统 (core/event_system.py) 进行组件通信
- 性能监控通过 core/performance_monitor.py 实现

#### UI现代化参考
- 参考云外端 (external_client.py) 和现代化云内端的 CustomTkinter 实现
- 使用 ui/components/ 下的可复用组件库
- 采用LocalSend风格的卡片式设计
- 保持向后兼容性 (fallback到传统Tkinter)

#### 测试和调试
- 现代化版本测试文件: test_modern_ui.py, test_card_components.py, test_responsive_layout.py
- 使用 start_modern_intranet.bat 启动现代化版本进行测试
- 自动fallback机制确保兼容性

#### 性能优化
- 使用流式处理避免大文件内存问题
- 实现异步架构防止UI冻结
- 优化轮询算法减少服务器负载

#### 新功能开发
- 在 network_utils.py 中添加核心网络功能
- 更新 config.ini 添加新配置项
- 确保加密安全性和向后兼容

### 测试和调试
- 现代化版本测试文件: test_modern_ui.py, test_card_components.py, test_responsive_layout.py
- 使用 start_modern_intranet.bat 启动现代化版本进行测试
- 自动fallback机制确保兼容性
- 性能监控和健康检查内置于现代化版本

### 文档和架构参考
- `README.md`: 项目总览和快速开始
- `project-architecture.md`: 原始架构分析
- `UPGRADE_RECORD.md`: 云外端完整改造记录
- `MODERNIZATION_COMPLETION_REPORT.md`: 云内端现代化改造完成报告

## 安全注意事项

- 密钥通过 keyring 安全存储，不在代码中硬编码
- 所有文件传输都经过 Fernet 对称加密
- Cookie同步机制依赖本地服务器，需注意网络安全
- 配置文件中不包含敏感信息，仅存储URL和功能配置

## 已知技术债务

1. **自动化测试**: 现有手动测试文件需要扩展为完整的自动化测试套件
2. **Cookie同步**: 依赖浏览器脚本的机制较为脆弱
3. **代码重构**: 传统版本 (intranet_gui_client.py) 仍保留作为fallback，未来可考虑完全移除

## 架构状态

### ✅ 已完成
- 云外端现代化改造 (v5.9)
- 云内端现代化改造 (v5.0 MVP架构)
- UI与业务逻辑分离
- CustomTkinter现代化界面
- 异步处理和事件驱动架构

### 🔄 持续改进
- 自动化测试覆盖率提升
- 用户体验优化
- 性能监控完善


