# 🗺️ DSH MCP Map Router

> **Map-First Just-In-Time (JIT) Tool Routing for DeepSeek Harness (DSH) and Modern AI Agent Runtimes.**
>
> 🚀 *Eliminate the Tool Context Tax. Zero prompt bloat, zero hallucinated tool calls, instant execution.*

---

## 📌 The Problem: The "Tool Context Tax"

As AI agent developers equip their agents with more capabilities via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), a major architectural bottleneck arises:

1. **Static Prompt Bloat**: Registering 5 to 10 typical MCP servers (e.g., meeting managers, document parsers, database clients, browser automation) injects **30,000 to 60,000 tokens of raw JSON tool schemas** into every turn of conversation.
2. **First-Token Latency**: The LLM must ingest the entire "weapons manual" on every single turn—even for a simple query like *"What is 2+2?"*
3. **The Flaw of Naive ToolRouters**: Some open-source projects attempt pure dynamic routing via meta-tools (`search_tools()`). In practice, this forces a **"Two-Turn Latency Tax"** (Step 1: AI searches tools -> Step 2: AI calls tool), doubling response time from 5s to 15s+, and frequently misses tools due to semantic retrieval ambiguity.

```
[ Traditional Static MCP ]
Prompt = [ 50,000 Tokens of Tool Schemas ] + [ "User Message" ]
Result: Slow, expensive, degraded attention.

[ Naive Dynamic ToolRouter ]
User: "Summarize meeting" ──► AI: search_tools("meeting") ──► Wait 10s ──► AI: call_tool()
Result: Multi-turn latency penalty, fragile recall.

[ DSH Map-First JIT Router (This Project) ]
User: "Summarize meeting" ──► Fast Asset Map Scan (<5ms) ──► JIT Mount ──► Native Direct Call
Result: 0 Token waste in idle turns, 100% credentialed recall, single-step execution!
```

---

## 💡 The Solution: Map-First JIT Routing

`dsh-mcp-map-router` introduces a tiered, deterministic architecture:

1. **L1 Local Asset Map (`mcp_registry.json`)**:
   Maintains a verified catalog of available MCP servers, their credentials, category profiles, and fast keyword/intent triggers.
2. **L2 Just-In-Time Slot Mounting**:
   The active agent session only loads core, lightweight tools by default (e.g., basic reasoning or OS bridge). Heavy domain tools are mounted **Just-In-Time** only when intent triggers match, and automatically detached when idle.
3. **L3 Market Discovery (Optional Fallback)**:
   External marketplaces or dynamic tool finders are only invoked if the local Asset Map yields zero matches.

### Performance Comparison

| Metric | All-in-One Static MCP | Naive Dynamic Router | Map-First JIT Router (Ours) |
| :--- | :---: | :---: | :---: |
| **Idle Context Tax** | 30k ~ 60k tokens | ~500 tokens | **~200 tokens (Minimal)** |
| **Execution Steps** | 1 step | 2+ steps (Search + Exec) | **1 step (Direct JIT)** |
| **First-Token Latency** | Slow (Heavy prompt) | Extremely Slow (2 turns) | **Fast (< 1s cold start)** |
| **Credential Reliability** | 100% | Often unauthenticated | **100% (Pre-verified)** |
| **Hallucination Risk** | High (Context confusion)| High (Mismatched schema)| **Near Zero** |

---

## 📁 Repository Structure

```text
dsh-mcp-map-router/
├── src/
│   └── index.ts               # DeepSeek Harness (Cordis) Plugin implementation
├── python/
│   └── mcp_map_router.py      # Standalone universal CLI engine (Antigravity/Cursor/Claude)
├── mcp_registry.example.json  # Sanitized Asset Map schema specification
├── package.json               # DSH plugin package definition
├── LICENSE                    # MIT License
└── README.md                  # Project documentation
```

---

## 🚀 Quick Start

### 1. In DeepSeek Harness (DSH / Cordis)

Install the plugin into your DeepSeek Harness environment:

```bash
npm install dsh-plugin-map-router
```

Add configuration to your `cordis.yml` or plugin manager:

```yaml
plugins:
  mcp-map-router:
    registryPath: './config/mcp_registry.json'
    autoMount: true
    scoreThreshold: 3
    keepAliveTurns: 2
```

### 2. Standalone Universal CLI (Antigravity, Claude Code, Cursor, OpenCode)

Copy `mcp_registry.example.json` to `mcp_registry.json` and configure your tools:

```bash
cp mcp_registry.example.json mcp_registry.json
```

Run CLI operations:

```bash
# Check current active vs dormant tools
python3 python/mcp_map_router.py status

# List predefined profile presets
python3 python/mcp_map_router.py list

# Switch to a lightweight profile
python3 python/mcp_map_router.py use minimal

# Scan intent and auto-mount Just-In-Time
python3 python/mcp_map_router.py scan "Need to export meeting attendees" --mount
```

---

## ⚙️ Asset Map Specification (`mcp_registry.json`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "version": "1.0.0",
  "default_profile": "minimal",
  "profiles": {
    "minimal": ["core-evaluator"],
    "office": ["core-evaluator", "meeting-assistant"]
  },
  "servers": {
    "meeting-assistant": {
      "displayName": "Enterprise Meeting Assistant",
      "category": "office",
      "description": "Meeting scheduling and transcript extraction",
      "toolsCount": 28,
      "tags": ["meeting", "transcripts", "schedule", "minutes"],
      "intentPatterns": ["meeting transcript", "schedule meeting"],
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

## 🤝 Contributing

We welcome issues and pull requests! Whether adding adapter support for additional agent frameworks (LangGraph, AutoGen, CrewAI) or improving intent classification algorithms, your contributions are appreciated.

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
