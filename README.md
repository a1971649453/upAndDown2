# upAndDown2 云剪切板工具 📋

> **安全的文件传输解决方案** - 支持内网上传，外网下载的跨网络文件传输工具

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![UI Framework](https://img.shields.io/badge/UI-CustomTkinter-green.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

## 🎯 项目简介

upAndDown2 是一个现代化的云剪切板工具，专为解决内外网隔离环境下的文件传输问题而设计。通过安全的加密通道，实现内网文件上传和外网文件下载的无缝连接。

### ✨ 核心特性

- 🔒 **安全加密传输** - 采用Fernet对称加密，保障文件传输安全
- 🎨 **现代化界面** - LocalSend风格设计，清新简约的用户体验
- 🎨 **动态状态指示** - 智能颜色变化的状态指示器
- ⚡ **高性能处理** - 异步架构，支持大文件分片传输
- 🔄 **智能轮询** - 自适应轮询间隔，降低服务器负载
- 🎯 **拖拽上传** - 支持文件拖拽，一键上传操作
- 📊 **实时监控** - 内置性能监控和健康检查
- 🔧 **自动回退** - 现代化UI与传统UI双重保障
- 🎨 **动态状态指示** - 智能颜色变化的状态指示器

### 🏗️ 技术架构

- **编程语言**: Python 3.8+
- **UI框架**: CustomTkinter (现代化) + Tkinter (兼容)
- **架构模式**: MVP (Model-View-Presenter) 分层架构
- **网络通信**: requests + requests-toolbelt
- **加密安全**: cryptography (Fernet) + keyring
- **异步处理**: ThreadPoolExecutor + asyncio

## 📦 快速安装

### 方式一：一键安装（推荐）

1. **下载项目**
   ```bash
   git clone <repository-url>
   cd upAndDown2
   ```

2. **运行一键安装脚本**
   ```bash
   # Windows环境
   一键安装.bat
   ```

### 方式二：手动安装

1. **环境要求**
   - Python 3.8 或更高版本
   - Windows 10/11 操作系统

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **初始化配置**
   ```bash
   python config_setup.py
   ```

### 方式三：离线环境部署

1. **在有网络的环境中准备离线包**
   ```bash
   # 下载离线依赖包
   下载离线包.bat
   ```

2. **在离线环境中安装**
   ```bash
   # 将offline_packages目录复制到离线环境
   # 运行离线安装脚本
   离线安装.bat
   ```

## 🚀 使用指南

### 首次配置

运行配置向导，设置加密密钥和服务器地址：

```bash
python config_setup.py
```

**重要**: 确保云内端和云外端使用相同的加密密钥！

### 云内端（上传端）使用

#### 现代化版本（推荐）
```bash
# 启动现代化云内端
start_optimized_uploader.bat
```

**功能特性**:
- ✅ 现代化CustomTkinter界面
- ✅ 拖拽文件上传
- ✅ 智能重复检测
- ✅ 实时进度显示
- ✅ 性能监控
- ✅ 响应式布局设计

#### 传统版本（兼容）
```bash
# 启动传统云内端
启动上传工具.bat
```

### 云外端（下载端）使用

```bash
# 启动云外端
start_optimized_uploader.bat
```

**功能特性**:
- 📥 自动文件检测和下载
- 🔍 智能轮询机制
- 📊 下载进度显示
- 🔧 自动错误恢复
- 🎨 LocalSend风格界面
- 🎯 动态状态指示器

### Cookie同步服务

```bash
# 启动Cookie同步服务器
start_cookie_server.bat
```

配合浏览器脚本 `wisedu-cookie-sync.user.js` 使用，实现Cookie自动同步。

## 📋 详细使用流程

### 完整文件传输流程

#### 步骤1: 环境准备

1. **云内端环境**（有内网权限的计算机）
   - 运行 `一键安装.bat` 或手动安装依赖
   - 运行 `python config_setup.py` 完成初始配置

2. **云外端环境**（有外网权限的计算机）
   - 同样完成安装和配置
   - ⚠️ **重要**: 确保使用相同的加密密钥

#### 步骤2: 启动服务

1. **云内端**
   ```bash
   # 启动现代化上传端（推荐）
   yunei.bat
   
   # 或启动传统上传端
   启动上传工具.bat
   ```

2. **云外端**
   ```bash
   # 启动下载端
   yunwai.bat
   ```

3. **Cookie同步**（可选）
   ```bash
   # 启动Cookie同步服务
   start_cookie_server.bat
   ```

#### 步骤3: 文件传输

1. **上传文件**
   - 在云内端界面中选择文件或直接拖拽文件
   - 点击"上传"按钮或使用一键上传
   - 等待上传完成确认

2. **下载文件**
   - 云外端会自动检测到新上传的文件
   - 选择要下载的文件
   - 文件自动下载到 `downloads/` 目录

#### 步骤4: 安全清理

- 下载完成后，建议删除服务器上的临时文件
- 云外端提供一键清理功能

## ⚙️ 配置说明

### config.ini 配置文件

```ini
[DEFAULT]
# 服务器配置
upload_url = http://your-server.com/upload
query_url = http://your-server.com/query
base_download_url = http://your-server.com
delete_url_template = http://your-server.com/delete/{file_id}

# 本地配置
download_dir = ./downloads/

# 轮询配置
base_poll_interval = 5          # 基础轮询间隔(秒)
max_poll_interval = 60          # 最大轮询间隔(秒)
poll_increase_factor = 1.5      # 轮询间隔递增因子
auto_stop_minutes = 10          # 自动停止时间(分钟)

# 文件配置
max_file_size_mb = 6           # 最大文件大小(MB)
chunk_size_mb = 3              # 分片大小(MB)
```

### 高级配置选项

- **智能轮询**: 动态调整查询间隔，减少服务器压力
- **分片传输**: 大文件自动分片，提高传输成功率
- **自动重试**: 网络异常时自动重试机制
- **性能监控**: 实时监控应用性能指标

## 🔧 故障排除

### 常见问题

#### 1. 启动失败
```bash
# 检查Python版本
python --version

# 检查依赖安装
pip list | findstr "customtkinter\|requests\|cryptography"

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

#### 2. 现代化界面无法启动
- 自动回退到传统界面
- 检查CustomTkinter安装: `pip install customtkinter>=5.2.0`
- 查看启动脚本的错误信息

#### 3. 配置问题
```bash
# 重新运行配置向导
python config_setup.py

# 检查config.ini文件
# 验证keyring中的密钥存储
```

#### 4. 文件传输失败
- 检查网络连接
- 验证服务器地址配置
- 确认文件大小未超出限制
- 检查加密密钥是否一致

#### 5. Cookie同步问题
- 确保Cookie同步服务已启动
- 检查浏览器脚本是否正确安装
- 验证本地服务器端口(默认8080)

### 调试模式

启动应用时添加调试参数：
```bash
python intranet_gui_client_optimized.py --debug
python external_client.py --debug
```

### 日志查看

- 应用日志: 控制台输出
- 性能监控: 现代化版本内置监控面板
- 错误信息: 详细的用户友好错误提示

## 📁 项目结构

```
upAndDown2/
├── 📄 README.md                    # 项目使用文档
├── 📄 CLAUDE.md                    # 开发者指南
├── 📄 MODERNIZATION_COMPLETION_REPORT.md  # 现代化改造报告
├── 📄 UPGRADE_RECORD.md            # 升级记录
├── 📄 UPGRADE_RECORD.md            # 升级记录
├── 📄 requirements.txt             # Python依赖清单
├── 📄 config.ini                   # 配置文件
│
├── 🔧 一键安装.bat                 # 一键安装脚本
├── 🔧 离线安装.bat                 # 离线环境安装脚本
├── 🔧 下载离线包.bat               # 离线依赖包下载器
├── 🔧 yunwai.bat # 优化版启动脚本
├── 🔧 start_cookie_server.bat      # Cookie同步服务启动脚本
│
├── 🐍 intranet_gui_client_optimized.py  # 优化版云内端主程序 (v5.1)
├── 🐍 external_client.py           # 云外端主程序 (v5.9)
├── 🐍 intranet_gui_client.py       # 传统云内端主程序 (v4.0)
├── 🐍 config_manager.py            # 配置管理器
├── 🐍 config_setup.py              # 配置向导
├── 🐍 network_utils.py             # 网络工具函数
│
├── 🏗️ ui/                          # 现代化UI架构
│   ├── main_window.py              # 主窗口框架
│   ├── views/                      # 视图层
│   ├── controllers/                # 控制器层
│   ├── components/                 # UI组件库
│   ├── layouts/                    # 响应式布局
│   └── themes/                     # 主题管理
│
├── 🔧 services/                    # 业务服务层
│   ├── file_service.py             # 文件上传服务
│   ├── clipboard_service.py        # 剪切板服务
│   └── smart_assistant.py          # 智能助手
│
├── ⚙️ core/                        # 核心系统
│   ├── event_system.py             # 事件系统
│   └── performance_monitor.py      # 性能监控
│
├── 🌐 wisedu-cookie-sync.user.js   # 浏览器Cookie同步脚本
│
└── 📁 downloads/                   # 下载文件存储目录
    └── 📁 temp_chunks/             # 分片临时文件目录
```

## 🔒 安全说明

### 加密机制
- **对称加密**: 使用Fernet算法对文件内容进行加密
- **密钥管理**: 通过系统keyring安全存储密钥
- **传输安全**: 所有网络传输数据均经过加密

### 隐私保护
- 密钥不会以明文形式存储在配置文件中
- 文件在本地加密后再上传
- 支持文件传输后自动清理

### 安全建议
- 定期更换加密密钥
- 及时清理服务器上的临时文件
- 在不可信网络环境中谨慎使用

## 📈 版本说明

### 当前版本状态

| 组件 | 版本 | 状态 | 特性 |
|------|------|------|------|
| **云外端** | v5.9 | ✅ 已现代化 | CustomTkinter界面 + 智能轮询 + 动态状态指示 |
| **云内端优化版** | v5.1 | ✅ 已完成 | MVP架构 + 拖拽上传 + 性能监控 + 响应式布局 |
| **云内端传统版** | v4.0 | 🔧 兼容保留 | 传统Tkinter界面 + 基础功能 |

### 更新日志

#### v5.9 (云外端) - 2024年
- 🎨 LocalSend风格界面设计，清新简约
- ⚡ 智能轮询机制优化，自适应间隔调整
- 🔧 自动错误恢复和性能监控
- 📊 实时下载进度显示
- 🎯 动态状态指示器，智能颜色变化
- 🎨 优化UI颜色搭配，更加协调美观

#### v5.1 (云内端优化版) - 2024年
- ✨ MVP架构重构，UI与业务逻辑完全分离
- 🎨 CustomTkinter现代化界面
- 🎯 拖拽文件上传功能
- 🧠 智能重复检测和文件分析
- ⚡ 异步处理架构
- 📊 实时性能监控
- 🔄 事件驱动系统
- 📱 响应式布局设计

#### v5.0 (云内端现代化版) - 2024年
- ✨ MVP架构重构，UI与业务逻辑完全分离
- 🎨 CustomTkinter现代化界面
- 🎯 拖拽文件上传功能
- 🧠 智能重复检测和文件分析
- ⚡ 异步处理架构
- 📊 实时性能监控
- 🔄 事件驱动系统

## 🤝 贡献指南

### 开发环境设置

1. **克隆仓库**
   ```bash
   git clone <repository-url>
   cd upAndDown2
   ```

2. **安装开发依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行测试**
   ```bash
   python test_modern_ui.py
   python test_card_components.py
   python test_responsive_layout.py
   ```

### 开发指南
- 参考 `CLAUDE.md` 了解项目架构
- 查看 `MODERNIZATION_COMPLETION_REPORT.md` 了解现代化改造详情
- 基于现代化版本 (MVP架构) 进行新功能开发
- 确保向后兼容性

## 📞 技术支持

### 获取帮助
- 📖 查看本文档的故障排除章节
- 🔍 检查控制台输出的错误信息
- 📝 查看 `CLAUDE.md` 获取开发者信息

### 问题反馈
如遇到问题，请提供以下信息：
- 操作系统版本
- Python版本
- 错误信息截图
- 操作步骤描述

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

**维护团队**: Zwjin
**项目状态**: 活跃开发中  
**最后更新**: 2024年12月

---

🎉 **感谢使用 upAndDown2 云剪切板工具！**