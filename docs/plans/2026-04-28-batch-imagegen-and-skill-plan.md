# 批量生图与外部 Skill 接入计划

> 创建日期: 2026-04-28
> 状态: 进行中
> 关联当前入口: `docs/roadmap.md`

## 一、背景

当前插画链路已经支持：

- prompt pack / template / modifier / policy 解析
- `illustration prompt`
- `illustration generate`
- 同一 prompt 的 `--batch-count` 重复生成

但还缺两层关键能力：

1. 跨多个 chapter / entity 的批量任务协议
2. 面向两类消费端的统一批量交付方式
   - `webui-manual`
   - `external-agent`

同时，外部 skill 需要保持薄层，不能自己发明第二套任务协议或状态系统。

## 二、目标

1. 为插画系统补齐 canonical batch manifest
2. 让 `webui-manual` 和 `external-agent` 共用同一批量任务真相源
3. 提供配套 adapter skill，让外部 agent 直接消费仓库导出的 manifest
4. 保持现有 `illustration generate` 与 `--batch-count` 向后兼容

## 三、非目标

- 不在本轮改 UI 交互
- 不在本轮做新的在线 provider 接入
- 不在本轮做复杂任务队列、并发调度或远程回调系统
- 不让 adapter / skill 成为新的执行 owner

## 四、适用规则

- 当前执行入口：`docs/roadmap.md`
- 架构护栏：`docs/ARCHITECTURE_GUARDRAILS.md`
- protocol owner：文件协议、默认结构、路径约定
- commands owner：批量 spec/manifest 文件 I/O、CLI 输出、历史回录
- services owner：纯函数式批量清单与投递说明组装
- adapters owner：面向宿主的薄 skill 文档与引用说明
- 不变量：
  - `services/` 不做文件 I/O
  - adapter 不得引入并行真相源
  - `illustrations.yaml` 继续是真实生成历史的 owner
  - JSON-compatible YAML 约束继续有效

## 五、设计结论

### 5.1 两条执行路径，共用一个 manifest

新增 batch manifest 作为批量任务的唯一真相源。

同一份 manifest 可以被：

- `webui-manual` 消费：人工复制 prompt / negative prompt / 参数到 WebUI，并把图片写回 manifest 指定路径
- `external-agent` 消费：外部 agent 通过配套 skill 读取 manifest，逐条生成，并把图片写回 manifest 指定路径

CLI 再通过 `batch-record` 把落盘结果回录到 `illustrations.yaml`。

### 5.2 批量协议分三层

1. `batch spec`
   - 用户声明“要生成哪些目标”和默认参数
2. `batch manifest`
   - CLI 解析 project state + prompt pack 后得到的最终任务清单
3. `generated history`
   - 图片真正落盘后，通过 CLI 回录到 `illustrations.yaml`

### 5.3 回录优先于外部状态

外部 WebUI 或 agent 只需要：

1. 读取 manifest
2. 按 manifest 指定路径输出图片

不要求外部工具维护额外会话数据库。仓库内仍以：

```text
story-canvas CLI -> illustrations.yaml
```

作为最终历史 owner。

## 六、实现范围

### 6.1 Protocol

- 扩展 `illustrations.yaml` 默认结构，新增 `batchSystem`
- 约定批量导出默认 delivery mode 与外部 skill 名称
- 约定默认 manifest 路径生成规则

### 6.2 Services

- 新增纯函数，负责：
  - 规范化 batch spec
  - 生成 manifest summary
  - 生成 `webui-manual` / `external-agent` 投递说明

### 6.3 Commands

- 新增 `illustration batch-export`
- 新增 `illustration batch-record`
- `illustration config` 增加批量相关默认配置读写
- `illustration list` / config payload 暴露 `batchSystem`

### 6.4 Adapters

- 新增 `story-canvas-imagegen` skill
- 至少提供：
  - `SKILL.md`
  - `references/cli.md`
  - Codex `agents/openai.yaml`
- 说明两条路径：
  - 单图仍可直接 `illustration generate`
  - 批量优先 `batch-export -> generate -> batch-record`

## 七、拟定 CLI 方案

### 7.1 `illustration batch-export`

输入：

- `--root`
- `--spec <json-compatible-yaml>`
- `--delivery-mode webui-manual|external-agent`
- `--output <manifest-path>` 可选

输出：

- 解析后的 batch manifest
- 每个 job 的：
  - resolved payload
  - prompt snapshot
  - provider request
  - output files
  - delivery-specific instructions

### 7.2 `illustration batch-record`

输入：

- `--root`
- `--manifest <path>`

行为：

- 检查 manifest 声明的输出文件是否存在
- 将存在的资产写入 `illustrations.generated[]`
- 保留 manifest 中的 prompt/provider snapshot 作为回溯依据

## 八、batch spec 草案

```json
{
  "label": "volume-1-scenes",
  "defaults": {
    "mode": "text-to-image",
    "templateId": "scene-standard",
    "commercialMode": "personal",
    "batchCount": 1
  },
  "jobs": [
    {
      "chapterId": "chapter-001",
      "extraPrompt": "雨夜码头，强调冷白灯与潮湿反光"
    },
    {
      "entityId": "char-linzhou",
      "templateId": "character-standard"
    }
  ]
}
```

## 九、兼容策略

- 现有 `illustration generate` 保持不变
- 现有 `--batch-count` 继续表示“单个目标的同模板重复生成”
- 老项目没有 `batchSystem` 时，自动回填默认值

## 十、验证计划

- 新增插画 batch export / record smoke tests
- 回归现有 `illustration generate` smoke tests
- adapter 安装脚本至少做一次 dry-run 验证

## 十一、风险

### 11.1 架构风险

若让 WebUI 或 skill 单独维护批量 job 结构，会立即形成并行真相源。

### 11.2 兼容风险

`illustrations.yaml` 新增字段后，旧项目必须无迁移可读。

### 11.3 交付风险

如果没有 `batch-record`，手工 WebUI 和外部 agent 流只能生成文件，无法安全回录项目历史。

## 十二、回滚路径

- 新增子命令和新字段均为增量接入
- 如需回滚，可单独移除 batch manifest 路径，不影响现有单图生成能力
