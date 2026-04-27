# Image Prompt System Protocol

> 最后更新: 2026-04-27
> 状态: 提议中（协议设计，尚未完整实现）
> 关联: `docs/roadmap.md`, `docs/plans/2026-04-27-lightweight-image-workbench-prd.md`

## 1. 目标

为生图工作台定义一套轻量、可复用、可拆分的提示词协议，满足以下要求：

- 降低用户使用门槛：模板优先，不从空白 prompt 开始
- 支持文生图、图生图、批量生图、重绘
- 兼容 `Story Canvas` 内嵌态与未来独立在线工具
- 保持 JSON-compatible YAML，不引入新型复杂 DSL

## 2. 设计原则

### 2.1 两层分离

协议分为两层：

1. `project state layer`
   - 项目级默认配置
   - 任务历史
   - 选中的 pack/template/modifier 引用
2. `prompt pack resource layer`
   - 可复用模板资源
   - 可被内嵌工作台和未来独立工具共同消费

### 2.2 模板优先

- 用户默认不直接编辑完整 prompt
- 系统先选择模板，再接受用户追加描述

### 2.3 快照可复现

- 每次生成记录必须保存解析后的 prompt 快照
- 后续即使 pack 更新，旧历史仍应可复现和回溯

### 2.4 可商用扩展

- 普通版与商业版的差异优先体现在模板包、策略约束和输出规范
- 不在核心协议里硬编码具体计费或账户模型

## 3. 文件布局

### 3.1 项目内可选文件

```text
story-project/
  illustrations.yaml
  prompts/
    illustration-packs/
      pack-default.yaml
      pack-light-novel.yaml
```

说明：

- `illustrations.yaml` 继续作为项目级配置与任务历史的真相源
- `prompts/illustration-packs/*.yaml` 是项目内可选 pack 资源
- 若项目目录下没有自定义 pack，必须回退 builtin packs

### 3.2 当前兼容策略

- 新协议不要求现有项目立即迁移
- 老项目只有 `illustrations.yaml` 也必须正常工作
- pack 资源缺失时，系统回退 builtin `default`

## 4. `illustrations.yaml` 协议扩展

### 4.1 当前结构

当前 `illustrations.yaml` 已维护：

- `adapter`
- `promptPack`
- `generated`

### 4.2 提议结构

```json
{
  "adapter": {
    "name": "openai",
    "model": "gpt-image-2",
    "defaultSize": "1024x1024",
    "quality": "standard"
  },
  "promptSystem": {
    "defaultPack": {
      "source": "builtin",
      "packId": "story-canvas/default",
      "version": "1.0"
    },
    "defaultTemplateByUseCase": {
      "character": "character-standard",
      "chapter-scene": "scene-standard",
      "promo": "promo-standard"
    },
    "defaultModifierRefs": [],
    "commercialMode": "personal"
  },
  "batchSystem": {
    "defaultDeliveryMode": "webui-manual",
    "externalAgentSkill": "story-canvas-imagegen"
  },
  "generated": []
}
```

### 4.3 字段说明

- `promptSystem.defaultPack`
  - 默认使用的 prompt pack
- `promptSystem.defaultTemplateByUseCase`
  - 各用途的默认模板
- `promptSystem.defaultModifierRefs`
  - 默认修饰器引用
- `promptSystem.commercialMode`
  - `personal` / `commercial`
- `batchSystem.defaultDeliveryMode`
  - `webui-manual` / `external-agent`
- `batchSystem.externalAgentSkill`
  - 外部 agent 模式默认 skill 名称

### 4.4 兼容关系

- `promptPack` 可保留为旧字段兼容层
- 新实现优先消费 `promptSystem`
- 读旧项目时可把 `promptPack.name/version` 映射到 `promptSystem.defaultPack`

## 5. Prompt Pack 资源协议

### 5.1 最小结构

每个 pack 文件必须是合法 JSON，建议结构如下：

```json
{
  "id": "story-canvas/default",
  "version": "1.0",
  "label": "Default Narrative Pack",
  "description": "基础叙事型生图模板包",
  "supports": {
    "modes": ["text-to-image", "image-to-image", "inpaint"],
    "commercial": true
  },
  "templates": [],
  "modifierGroups": [],
  "policies": {}
}
```

### 5.2 顶层字段

- `id`
  - pack 全局标识
- `version`
  - pack 版本
- `label`
  - 显示名称
- `description`
  - 简短说明
- `supports`
  - 支持的模式与商业能力
- `templates`
  - 模板列表
- `modifierGroups`
  - 修饰器分组
- `policies`
  - 负向、安全、商业约束

## 6. Template 协议

### 6.1 最小结构

```json
{
  "id": "character-standard",
  "label": "角色设定图",
  "useCase": "character",
  "complexity": "standard",
  "mode": "text-to-image",
  "promptTemplate": "{subject}\n{styleModifiers}\n{userExtraPrompt}",
  "defaultNegativePolicyRef": "default-safe",
  "defaultCommercialPolicyRef": "personal-default"
}
```

### 6.2 必填字段

- `id`
- `label`
- `useCase`
- `complexity`
- `mode`
- `promptTemplate`

### 6.3 `useCase` 枚举

- `character`
- `chapter-scene`
- `cover-concept`
- `promo`
- `product`

### 6.4 `complexity` 枚举

- `quick`
- `standard`
- `detailed`

### 6.5 `mode` 枚举

- `text-to-image`
- `image-to-image`
- `inpaint`

说明：

- `batch` 不是独立 mode，而是生成任务参数
- `inpaint` 对应重绘 / 局部重绘

## 7. Modifier 协议

### 7.1 目标

modifier 用于提供轻量、多样化但可控的修饰层，而不是让用户拼接无穷自由文本。

### 7.2 分组结构

```json
{
  "id": "style-anime",
  "group": "style",
  "label": "动漫",
  "promptFragment": "anime illustration, clean line art, expressive face",
  "negativeFragment": "",
  "commercialTags": []
}
```

### 7.3 `group` 建议枚举

- `style`
- `camera`
- `lighting`
- `composition`
- `material`
- `brand`

### 7.4 使用规则

- modifier 默认多选，但应允许 pack 自定义限制
- 某些商业 modifier 可要求 `commercialMode=commercial`

## 8. Policy 协议

### 8.1 目标

policy 用于承载负向提示、安全约束、商用限制，不把这些逻辑散落在 UI 字段里。

### 8.2 最小结构

```json
{
  "negativePolicies": [
    {
      "id": "default-safe",
      "label": "默认负向",
      "negativePrompt": "low quality, blurry, distorted hands"
    }
  ],
  "commercialPolicies": [
    {
      "id": "personal-default",
      "label": "个人默认",
      "mode": "personal",
      "extraPrompt": "",
      "restrictions": []
    }
  ]
}
```

### 8.3 商业模式

- `personal`
- `commercial`

商业模式的主要影响：

- 模板可用性
- modifier 可用性
- 默认约束与输出规范

## 9. 生成任务快照协议

### 9.1 目标

`generated[]` 中不能只记录最终 prompt 文本，还必须记录引用来源和展开结果。

### 9.2 建议结构

```json
{
  "id": "illust-001",
  "mode": "text-to-image",
  "targetRef": {
    "type": "chapter",
    "targetId": "chapter-001"
  },
  "promptSnapshot": {
    "packRef": {
      "source": "builtin",
      "packId": "story-canvas/default",
      "version": "1.0"
    },
    "templateRef": "scene-standard",
    "modifierRefs": ["style-anime", "lighting-night"],
    "userExtraPrompt": "雨夜街道，潮湿路面反光",
    "resolvedPrompt": "..."
  },
  "policySnapshot": {
    "negativePolicyRef": "default-safe",
    "commercialPolicyRef": "personal-default",
    "negativePrompt": "..."
  },
  "batch": {
    "count": 4,
    "variantStrategy": "same-template"
  }
}
```

### 9.3 快照要求

- 必须保存：
  - pack 引用
  - template 引用
  - modifier 引用
  - 用户追加提示词
  - 展开后的最终 prompt
- 建议保存：
  - negative / commercial policy 快照
  - batch 参数
  - edit / mask 参数

## 10. 批量与重绘协议

### 10.1 批量

批量生成属于任务参数，而不是 pack 资源本身：

```json
{
  "batch": {
    "count": 4,
    "variantStrategy": "same-template"
  }
}
```

建议枚举：

- `same-template`
- `modifier-variation`
- `prompt-variation`

当前实现额外约定：

- 批量任务先通过 `illustration batch-export` 导出 manifest
- `webui-manual` 与 `external-agent` 都必须消费同一份 manifest
- 最终生成历史通过 `illustration batch-record` 回录到 `illustrations.yaml`
- 资产落盘按 target type 自动整理：
  - `chapter` -> `assets/illustrations/chapters/<chapter-id>/`
  - `entity` -> `assets/illustrations/entities/<entity-id>/`
  - `temporary` -> `tmp/illustrations/staging/<temp-label>/`
- 默认命名由系统按 target type / useCase 推导；如需覆盖，仍使用 `--output-name` 或 batch spec `outputName`

### 10.2 重绘 / 局部重绘

建议落在任务层：

```json
{
  "edit": {
    "mode": "inpaint",
    "inputImages": ["assets/input/base.png"],
    "maskPath": "assets/input/mask.png"
  }
}
```

## 11. Builtin 与项目自定义

### 11.1 `source` 枚举

- `builtin`
- `project`
- `remote`（未来在线工具预留）

### 11.2 解析优先级

1. 显式任务指定
2. 项目默认 `promptSystem.defaultPack`
3. builtin `default`

## 12. 兼容与迁移

### 12.1 老项目

- 老项目不需要新增 `prompts/illustration-packs/`
- 老项目只有旧版 `promptPack` 字段时，仍可映射到默认 pack

### 12.2 渐进迁移

建议分阶段：

1. 先在协议文档中定义新字段
2. 再让 CLI / UI 开始读写 `promptSystem`
3. 最后再补项目内自定义 pack 加载与历史快照完善

## 13. 非目标

- 不定义复杂模板编程语言
- 不支持任意脚本执行
- 不把 provider 原始全部参数都塞进 pack 资源协议
- 不在协议层定义在线账户、计费、配额
