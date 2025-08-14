# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

upAndDown2 是一个安全的文件传输工具，支持内网上传和外网下载。该项目采用客户端-服务器架构，通过加密文件传输实现安全的数据交换。

### 核心组件
- **云外端 (external_client.py)**: 下载端应用，已升级到 v5.9 现代化版本
- **云内端 (intranet_gui_client.py)**: 上传端应用，当前为 v4.0，待现代化改造
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

# 云内端 (上传端) - 待现代化
启动上传工具.bat

# Cookie同步服务器
start_cookie_server.bat
```

## 技术架构

### 技术栈
- **编程语言**: Python 3.8+
- **UI框架**: 
  - 云外端: CustomTkinter (现代化) + Tkinter (兼容)
  - 云内端: Tkinter + ttkthemes (传统)
- **网络通信**: requests + requests-toolbelt
- **加密**: cryptography (Fernet对称加密)
- **凭证管理**: keyring
- **异步处理**: ThreadPoolExecutor + asyncio

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
├── intranet_gui_client.py  # 云内端主程序 (v4.0) ⏳待改造
├── network_utils.py        # 网络工具和加密功能
├── config_manager.py       # 配置管理和Cookie服务
├── config_setup.py         # 首次配置向导
├── config.ini              # 运行时配置文件
├── requirements.txt        # Python依赖清单
├── downloads/              # 下载文件存储目录
│   └── temp_chunks/        # 分片临时文件目录
├── yunwai.bat             # 云外端启动脚本
├── 启动上传工具.bat        # 云内端启动脚本
└── start_cookie_server.bat # Cookie服务启动脚本
```

## 开发指南

### 常见开发任务

#### UI现代化改造
- 参考云外端 (external_client.py) 的 CustomTkinter 实现
- 采用LocalSend风格的卡片式设计
- 实现色彩系统和组件库
- 保持向后兼容性 (fallback到传统Tkinter)

#### 性能优化
- 使用流式处理避免大文件内存问题
- 实现异步架构防止UI冻结
- 优化轮询算法减少服务器负载

#### 新功能开发
- 在 network_utils.py 中添加核心网络功能
- 更新 config.ini 添加新配置项
- 确保加密安全性和向后兼容

### 测试和调试
- 目前无自动化测试，依赖手动测试
- 使用 `.bat` 脚本快速启动应用进行测试
- 监控 config.ini 中的轮询配置效果

### 文档和架构参考
- `README.md`: 项目总览和快速开始
- `project-architecture.md`: 原始架构分析
- `UPGRADE_RECORD.md`: 云外端完整改造记录，可作为云内端改造参考

## 安全注意事项

- 密钥通过 keyring 安全存储，不在代码中硬编码
- 所有文件传输都经过 Fernet 对称加密
- Cookie同步机制依赖本地服务器，需注意网络安全
- 配置文件中不包含敏感信息，仅存储URL和功能配置

## 已知技术债务

1. **云内端现代化**: 当前UI与逻辑耦合，需要大规模重构
2. **测试覆盖**: 缺乏自动化测试，增加回归风险
3. **Cookie同步**: 依赖浏览器脚本的机制较为脆弱
4. **代码结构**: 部分业务逻辑与UI混合，需要进一步分离

## 改造优先级

### P0 (紧急)
- 云内端性能和稳定性问题修复
- 云内端UI现代化改造

### P1 (高优先级)
- 异步架构完善
- 单元测试框架搭建

### P2 (中优先级)
- 代码质量工具集成
- 用户体验优化
- 多语言支持