# upAndDown2 云剪切板工具

> 安全的内外网文件传输解决方案

## 🎯 项目简介

upAndDown2 是一个专为内外网隔离环境设计的文件传输工具，通过安全加密实现"内网上传，外网下载"的跨网络文件传输。

### 核心特性

- 🔒 **安全加密** - Fernet对称加密保障文件安全
- 🎨 **现代界面** - CustomTkinter现代化UI设计
- ⚡ **智能轮询** - 自适应间隔，降低服务器负载
- 🎯 **拖拽上传** - 支持文件拖拽和一键操作
- 📊 **实时监控** - 内置性能监控和状态反馈

## 📦 快速开始

### 环境要求
- Python 3.8+
- Windows 10/11

### 一键安装
```bash
# 在线安装（推荐）
一键安装.bat

# 离线环境安装
下载离线包.bat  # 在有网络环境运行
离线安装.bat    # 在离线环境运行
```

### 手动安装
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化配置
python config_setup.py
```

## 🚀 使用方法

### 云内端（上传）
```bash
# 启动优化版上传端
python intranet_gui_client_optimized.py
```

### 云外端（下载）
```bash
# 启动下载端
yunwai.bat
# 或
python external_client.py
```

### Cookie同步（可选）
```bash
# 启动Cookie同步服务
start_cookie_server.bat
```

## ⚙️ 配置文件

修改 `config.ini` 来调整设置：

```ini
# 轮询配置
base_poll_interval = 5      # 基础间隔(秒)
max_poll_interval = 60      # 最大间隔(秒)

# 文件配置  
max_file_size_mb = 6       # 最大文件大小(MB)
chunk_size_mb = 3          # 分片大小(MB)
```

## 🔧 常见问题

### 启动失败
```bash
# 检查Python版本
python --version

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### 界面无法显示
- 自动回退到传统Tkinter界面
- 检查CustomTkinter安装: `pip install customtkinter>=5.2.0`

### 文件传输失败
- 检查网络连接和服务器配置
- 确认加密密钥在两端一致
- 验证文件大小未超出限制

## 📁 项目结构

```
upAndDown2/
├── external_client.py              # 云外端（下载）
├── intranet_gui_client_optimized.py # 云内端优化版（上传）
├── config_manager.py               # 配置管理
├── network_utils.py                # 网络和加密工具
├── requirements.txt                # 依赖清单
├── ui/                            # 现代化UI组件
├── services/                      # 业务服务层  
├── core/                          # 核心系统
├── yunwai.bat                     # 云外端启动脚本
├── 一键安装.bat                   # 在线安装脚本
└── 离线安装.bat                   # 离线安装脚本
```

## 🔒 安全说明

- 所有文件传输均经过Fernet对称加密
- 密钥通过系统keyring安全存储，不在配置文件中明文保存
- 解密失败时只删除本地文件，保护其他用户的服务器文件

## 📈 版本信息

| 组件 | 版本 | 状态 |
|------|------|------|
| 云外端 | v5.9 | ✅ 现代化完成 |
| 云内端优化版 | v5.1 | ✅ UI优化完成 |

## 💡 使用建议

1. **首次使用**: 运行 `一键安装.bat` 进行自动配置
2. **安全设置**: 确保两端使用相同的加密密钥
3. **网络环境**: 离线环境使用离线安装包部署
4. **文件管理**: 优化版会自动清理已上传的文件

---

**维护**: 基于Claude Code开发  
**许可**: MIT License