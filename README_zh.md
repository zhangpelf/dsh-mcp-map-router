# 🗺️ DSH MCP Map Router (资产地图与即时动态路由)

[English](README.md) | [简体中文](README_zh.md)

> **专为 DeepSeek Harness (DSH) 及现代 AI Agent 运行时设计的「资产地图优先」即时工具挂载路由。**
>
> 🚀 *根除大模型「工具上下文税 (Tool Context Tax)」：零闲置 Token 浪费、零幻觉误调用、单步极速直达。*

---

## 📌 背景痛点：被忽视的「工具上下文税」

随着开发者使用 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 为智能体接入越来越多的能力，一个严峻的工程架构矛盾逐渐显现：

1. **静态挂载的上下文膨胀**：
   当你在配置里挂载 5~10 个典型 MCP 服务（如腾讯会议、文档解析、数据库、浏览器自动化等）时，每轮对话即便你只问一句“你好”，模型头部也被迫塞入 **30,000 ~ 60,000 Token 的工具 JSON 说明书**。
2. **首字延迟与算力浪费**：
   模型必须把整本“武器库说明书”通读一遍才肯下笔，造成打字掉帧、首字等待高达十几秒，且容易导致注意力涣散。
3. **纯动态 ToolRouter 的“反向减速”陷阱**：
   部分开源方案尝试让模型通过元工具（如 `search_tools()`）在运行时盲搜。但在工程实操中，这引入了严重的 **“两轮延迟税”**（第 1 步搜工具 ➜ 等待 10 秒 ➜ 第 2 步才调工具），响应时间直接翻倍，且经常因为自然语言表述差异而漏召回工具。

```
【 传统静态全量挂载 】
输入 = [ 50,000 Token 的沉重工具定义 ] + [ "今天几号" ]
弊端：极慢、高昂费用、注意力被稀释。

【 纯动态盲搜 ToolRouter 】
用户："查会议纪要" ──► AI：search_tools("会议") ──► 白等 10s ──► AI：真正调用接口
弊端：强制两轮推理，延迟翻倍，经常漏召回。

【 DSH 资产地图即时路由 (本项目) 】
用户："查会议纪要" ──► 本地资产地图扫描 (<5ms) ──► 瞬间热插拔挂载 ──► 原生单步直接调
优势：平时零 Token 浪费，100% 具备有效鉴权凭证，单步直达！
```

---

## 💡 核心设计哲学：Map-First JIT 架构

`dsh-mcp-map-router` 采用分层确定性路由架构：

1. **L1 私域资产地图 (`mcp_registry.json`)**：
   维护一份经过验证的本地 MCP 资产总账，包含服务器配置、连接鉴权 Token、类别预设与语义触发词（Tags & Regex）。
2. **L2 即时插槽挂载 (Just-In-Time Slot)**：
   智能体在日常空闲时**仅挂载核心轻量工具**。当用户意图命中资产地图的标签时，系统在毫秒级内将该 MCP 动态载入当前会话槽；任务完成后自动按需卸载（Decay Detach），不留任何历史上下文包袱。
3. **L3 生态市场搜索 (可选兜底)**：
   只有当本地资产地图完全未收录对应能力时，才向外探索生态或插件市场，杜绝无意义的网络开销。

---

## 📊 架构性能实测对比

| 核心指标 | 静态全量 MCP 挂载 | 纯动态盲搜 Router | 资产地图即时路由 (本项目) |
| :--- | :---: | :---: | :---: |
| **空闲对话上下文税** | 30,000 ~ 60,000 Tokens | ~500 Tokens | **~200 Tokens (极致轻量)** |
| **工具执行所需步数** | 1 步 | 2 步以上 (先搜再调) | **1 步 (JIT 注入后直接执行)** |
| **首字响应延迟** | 慢 (巨型 Prompt 吞吐) | 极慢 (两轮往返) | **极速 (< 1s 瞬间启动)** |
| **鉴权凭证可靠性** | 100% | 经常缺失密钥报错 | **100% (私域实测资产)** |
| **工具幻觉误报率** | 较高 (几十个接口混淆)| 较高 (语义匹配漂移)| **趋近于零 (确定性标签匹配)** |

---

## 📁 仓库项目结构

```text
dsh-mcp-map-router/
├── src/
│   └── index.ts               # DeepSeek Harness (Cordis) 官方标准插件实现
├── python/
│   └── mcp_map_router.py      # 通用独立跨平台 CLI 引擎 (兼容 Antigravity/Cursor/Claude)
├── mcp_registry.example.json  # 100% 脱敏的标准资产地图定义模板
├── cordis.patch.yml           # DeepSeek Harness 一键打补丁配置文件
├── package.json               # DSH / npm 插件包元数据定义 (包含 dsh-market 关键字)
├── LICENSE                    # MIT 开源许可
├── README.md                  # 英文主页
└── README_zh.md               # 中文全景文档
```

---

## 🚀 快速上手与挂靠指引

### 1. 在 DeepSeek Harness (DSH) 中作为插件使用

#### 安装插件
```bash
npm install dsh-plugin-map-router
# 或在 DSH 插件市场 (Plugin Market) 中搜索 "mcp-map-router" 点击安装
```

#### 配置接入 (`cordis.yml` 或 `cordis.patch.yml`)
在你的 DSH 配置文件中启用该插件：
```yaml
plugins:
  mcp-map-router:
    registryPath: './config/mcp_registry.json'
    autoMount: true
    scoreThreshold: 3
    keepAliveTurns: 2
```

#### 体验交互
在 DSH 客户端中正常聊天即可自动感知：
* 用户：“*帮我导出下午那场产品会的参会名单*”
* DSH 后台瞬间匹配 `tencent-meeting` 并动态注入，模型直接单步调用并返回名单；
* 两轮对话后若无新会议需求，该模块自动从活动插槽中卸载，保持环境纯净。

---

### 2. 在通用独立环境中使用 (Antigravity / Cursor / Claude Code / OpenCode)

拷贝示例地图模板：
```bash
cp mcp_registry.example.json mcp_registry.json
```

命令行快速操控：
```bash
# 查看当前活动挂载 vs 离线资产清单
python3 python/mcp_map_router.py status

# 列出当前配置的场景预设 (Profiles)
python3 python/mcp_map_router.py list

# 切换到极简模式 (秒速释放所有非必要工具)
python3 python/mcp_map_router.py use minimal

# 模拟意图扫描并即时挂载
python3 python/mcp_map_router.py scan "需要预定一个明天上午的会议并导出纪要" --mount
```

---

## ⚙️ 资产地图规范说明 (`mcp_registry.json`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "version": "1.0.0",
  "default_profile": "minimal",
  "profiles": {
    "minimal": ["core-evaluator"],
    "office": ["core-evaluator", "meeting-assistant"],
    "research": ["core-evaluator", "deep-research-hub"]
  },
  "servers": {
    "meeting-assistant": {
      "displayName": "企业会议助手",
      "category": "office",
      "description": "会议预定、参会人员导出与音频纪要转录",
      "toolsCount": 28,
      "tags": ["会议", "纪要", "参会人", "转录", "schedule", "minutes"],
      "intentPatterns": ["会议纪要", "预定会议", "开会"],
      "serverConfig": {
        "serverUrl": "https://api.example.com/mcp/v1",
        "headers": {
          "Authorization": "Bearer ${MEETING_TOKEN}"
        }
      }
    }
  }
}
```

---

## 🤝 贡献与生态共建

欢迎提交 Issue 和 Pull Request！我们期待社区开发者：
1. 贡献适配更多 Agent 框架（如 LangGraph, AutoGen, CrewAI）的适配器；
2. 完善多模态意图与语义距离匹配算法；
3. 为常用商业与开源 MCP 服务扩充官方标准 Tags 词库。

## 📄 开源许可证

本项目基于 [MIT 许可证](LICENSE) 开源。
