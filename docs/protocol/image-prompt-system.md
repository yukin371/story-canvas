# Image Prompt System Protocol

> 最后更新: 2026-04-28
> 状态: 部分已实现（首批模板矩阵已落地）
> 关联: `docs/roadmap.md`, `docs/plans/2026-04-28-illustration-template-matrix.md`

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
- 系统按 `小说类型 pack × 用途 template × modifier` 展开，而不是维护一个万能 prompt

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
- 若要在项目内定制 builtin/default pack，应先通过 `illustration pack-export` 或 UI 对应导出入口复制到项目作用域，再编辑该副本

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
      "character-sheet": "character-sheet-standard",
      "chapter-scene": "scene-standard",
      "cover-poster": "cover-poster-standard",
      "duel-scene": "duel-scene-standard",
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
- `cover-concept` 与 `product` 继续保留为兼容 use-case，但模板解析会优先走同类 fallback，而不是退成任意第一条模板

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
  "lexicon": {},
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
- `lexicon`
  - 可选词库层，承载自然化 prompt 所需的短语集合
- `templates`
  - 模板列表
- `modifierGroups`
  - 修饰器分组
- `policies`
  - 负向、安全、商业约束

### 5.3 `lexicon` 协议

目标：

- 把“常用视觉表达”从 `promptTemplate` 和命令层文本里抽出来，避免模板越写越像硬编码字符串
- 让角色设定图、章节场景图、宣传图共享一套可回溯、可替换的短语词库
- 降低 `visual direction:` / `user direction:` 这类标签式 prompt 的 AI 感

建议结构：

```json
{
  "subjectPhrases": {
    "character": ["人物辨识度", "稳定的外貌记忆点"],
    "chapter-scene": ["人物关系和动作焦点", "可读的空间层次"]
  },
  "detailPhrases": {
    "character": ["面部特征、发型和服饰材质"],
    "chapter-scene": ["光源方向、关键道具与环境质感"]
  },
  "modePhrases": {
    "text-to-image": ["不要写成分镜指令，直接给出能落图的画面印象。"],
    "image-to-image": ["以输入图的身份和结构为底，只调整镜头、质感和氛围。"]
  },
  "commercialPhrases": {
    "commercial": ["成片保持干净利落，避免影射现成品牌、Logo 和受保护角色元素。"]
  }
}
```

说明：

- 所有字段均可选，缺失时回退到 pack 内建最小词库或 service 层默认短语
- `subjectPhrases` / `detailPhrases` 通常按 `useCase` 分组
- 同一题材 pack 可以只细化自己关心的 use-case；未覆盖的 use-case 允许沿同类 fallback 链复用词库
- `modePhrases` 按 `mode` 分组
- `commercialPhrases` 按 `commercialMode` 分组
- `negativePhrases` 可选，供未来把负向短语也从 policy 文本里拆出来；当前不是必需字段
- 旧 pack 如果仍使用 `visual direction:`、`user direction:`、`{userExtraPrompt}`、`{commercialPrompt}` 这类旧模板写法，协议层加载与保存时会自动迁移到新 placeholder 风格；历史生成记录中的 `promptSnapshot` 不在本轮自动回写
- 推荐闭环为：导出 builtin/default pack 到项目目录 → 本地编辑模板/词库 → 必要时运行 `illustration pack-migrate` 统一到 canonical 模板 → 在 `illustrations.yaml.promptSystem.defaultPack` 中切回导出的 project pack

## 6. Template 协议

### 6.1 最小结构

```json
{
  "id": "character-standard",
  "label": "角色设定图",
  "useCase": "character",
  "complexity": "standard",
  "mode": "text-to-image",
  "promptTemplate": "{subject}\n先把{subjectPhrases}立住，再把{detailPhrases}交代清楚。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
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
- `character-sheet`
- `chapter-scene`
- `cover-concept`
- `cover-poster`
- `ensemble-key-visual`
- `duel-scene`
- `chase-escape`
- `comic-relief`
- `promo`
- `product`
- `prop-relic`
- `creature-sheet`
- `manga-panel`
- `manga-page`

并非每个 pack 都必须为每个 use-case 提供专用模板。当前解析器会优先做同类 fallback，避免“没配专用模板时误退到 pack 第一条模板”：

- `cover-concept -> cover-poster -> promo`
- `character-sheet -> character`
- `duel-scene -> chapter-scene`
- `product -> prop-relic -> promo -> character`
- `manga-page -> manga-panel -> chapter-scene -> promo`

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
- 新模板可以使用更自然的 placeholder，例如 `subjectPhrases`、`detailPhrases`、`modeHint`、`stylePrompt`、`userDirection`、`commercialDirection`
- 旧模板中的 `styleModifiers`、`userExtraPrompt`、`commercialPrompt` 仍保留兼容

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
