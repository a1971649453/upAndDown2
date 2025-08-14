# upAndDown2 项目架构文档

> **更新日期**: 2025年8月14日  
> **项目版本**: v5.9 (云外端) | v5.x (云内端)  
> **文档状态**: 最新 ✅  

## 📁 项目结构

```
upAndDown2/
├── 📄 README.md                    # 项目说明文档
├── 📄 UPGRADE_RECORD.md            # 云外端改造完整记录 ⭐
├── 📄 project-architecture.md      # 原始项目架构文档
├── 📄 requirements.txt             # Python依赖包列表
├── 📄 config.ini                   # 配置文件 (智能轮询配置)
├── 📄 .gitignore                   # Git忽略文件配置
│
├── 🔧 yunwai.bat                   # 云外端启动脚本 (v5.9)
├── 🔧 启动上传工具.bat             # 云内端启动脚本 (待升级)
├── 🔧 start_cookie_server.bat      # Cookie服务启动脚本
│
├── 🐍 external_client.py           # 云外端主程序 (v5.9) ✅已现代化
├── 🐍 intranet_gui_client.py       # 云内端主程序 (v5.x) ⏳待改造
├── 🐍 config_manager.py            # 配置管理器
├── 🐍 config_setup.py              # 配置向导
├── 🐍 network_utils.py             # 网络工具函数
│
├── 🌐 wisedu-cookie-sync.user.js   # 浏览器Cookie同步脚本
│
└── 📁 downloads/                   # 下载文件存储目录
    └── 📁 temp_chunks/             # 分片临时文件目录
```

## 🎯 项目概览

### 核心功能
- **安全文件传输**: 内网上传 → 外网下载的安全通道
- **分片传输**: 支持大文件分片上传和下载
- **智能轮询**: 动态调整轮询间隔，减少服务器压力
- **现代化UI**: LocalSend风格的清新简约界面

### 技术架构
- **编程语言**: Python 3.8+
- **UI框架**: CustomTkinter (现代化) + Tkinter (兼容)
- **网络通信**: requests + Session连接复用
- **异步处理**: ThreadPoolExecutor多线程架构
- **加密安全**: 基于keyring的密钥管理

## 🚀 快速开始

### 环境准备
```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装现代化UI组件 (v5.9新增)
pip install customtkinter
```

### 运行应用
```bash
# 云外端 (下载端) - 已现代化
yunwai.bat

# 云内端 (上传端) - 待现代化  
启动上传工具.bat
```

## 📊 版本对比

| 组件 | 当前版本 | 状态 | 特性 |
|------|----------|------|------|
| **云外端** | v5.9 | ✅ 已升级 | 现代化UI + 企业级性能 |
| **云内端** | v5.x | ⏳ 待升级 | 传统界面 + 基础功能 |

## 🛠️ 改造指南

### 云内端改造参考
详细的改造指南请参考 [`UPGRADE_RECORD.md`](./UPGRADE_RECORD.md) 文档，包含：

- 🔍 **问题诊断**: 性能瓶颈识别和解决方案
- 🎨 **UI现代化**: LocalSend风格设计实现
- ⚡ **性能优化**: 异步架构和毫秒级响应
- 📚 **技术细节**: 完整的代码实现和最佳实践

### 改造优先级
1. **P0**: 修复性能和稳定性问题
2. **P1**: UI现代化改造
3. **P2**: 性能优化和异步架构

## 📋 待办事项

### 云内端现代化 (高优先级)
- [ ] UI界面LocalSend风格改造
- [ ] 性能优化和异步处理
- [ ] 智能上传算法实现
- [ ] 错误处理机制完善

### 项目优化 (中优先级)  
- [ ] 单元测试框架搭建
- [ ] 代码质量工具集成
- [ ] 用户手册和API文档
- [ ] 多语言支持

### 高级特性 (低优先级)
- [ ] 插件化架构设计
- [ ] 云端同步功能
- [ ] 移动端适配
- [ ] 集群部署支持

## 🔗 相关文档

- [`UPGRADE_RECORD.md`](./UPGRADE_RECORD.md) - 云外端改造完整记录 ⭐
- [`project-architecture.md`](./project-architecture.md) - 原始项目架构文档
- [`requirements.txt`](./requirements.txt) - 依赖包列表
- [`config.ini`](./config.ini) - 配置文件说明

## 📞 技术支持

如有问题或建议，请参考:
- 📖 改造记录文档中的问题排查指南
- 🐛 Git提交历史中的实现细节
- 💡 代码注释中的技术说明

---

**维护团队**: Claude Code Assistant  
**项目状态**: 活跃开发中  
**更新频率**: 根据需求实时更新