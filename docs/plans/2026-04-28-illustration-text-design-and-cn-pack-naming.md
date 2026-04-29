# 插画模板包扩充 / 中文命名 / 文本设计层计划

## 背景

- 当前内置 prompt pack 只有 `default` / `light-novel` / `web-serial` 三套，虽然单包 use-case 已扩充，但题材维度仍偏少。
- 用户自定义 pack 的文件名和派生 pack id 目前被强制 ASCII slug 化，中文命名体验不完整。
- 当前插画系统只有“纯图 prompt”一条轨道，没有把“纯绘图”和“带标题/介绍等文字设计的版式图”拆成显式可控参数。

## 目标

1. 扩充 builtin prompt packs，覆盖更多小说题材。
2. 允许 prompt pack 使用中文文件名和中文派生命名，不再强制英文 slug。
3. 在不新增并行真相源的前提下，为插画请求增加可选的文本设计层：
   - 可显式关闭，生成纯绘图；
   - 可显式开启，允许标题 / 副标题 / 简介 / 字体风格提示参与 prompt；
   - 用户可完全留空，自行决定是否使用。

## 适用规则

- 当前执行入口：`docs/roadmap.md`
- 架构 owner：
  - pack 真相源与规范化仍归 `protocol/prompt_packs.py`
  - prompt 组装仍归 `services/illustration_prompting.py`
  - 请求编排与落盘仍归 `commands/illustration.py` 与本地 UI API
  - 前端只能消费协议与 API，不新增前端独占持久化真相源
- 不变量：
  - 项目 pack 仍落在 `prompts/illustration-packs/*.yaml`
  - UI 只是协议可视化壳
  - services 继续保持纯函数，不做文件 I/O
  - 新字段必须向后兼容旧 pack / 旧生成记录

## 计划改动

### 1. 内置模板包扩充

- 新增多题材 builtin prompt packs，优先覆盖：
  - `玄幻`
  - `言情`
  - `西幻`
  - `科幻`
- 每套至少覆盖封面 / 插画 / 设定图 / 对决 / 宣传等核心 use-case。

### 2. 中文命名支持

- 放宽 prompt pack 文件名规范化：
  - 保留中文、数字、字母；
  - 仅清理路径非法字符和多余分隔符。
- 放宽 project pack id 派生规则，使 `project/玄幻海报模板` 这类 id 可稳定生成与回显。
- 前端新建 / 编辑模板包时不再强制把文件名转成纯英文 slug。

### 3. 文本设计层

- 为插画请求增加可选字段：
  - `textDesignMode`
  - `titleText`
  - `subtitleText`
  - `bodyText`
  - `fontStyleHint`
- `services/illustration_prompting.py` 负责把这些字段转成自然语言 brief，并写入 `promptSnapshot`。
- 历史记录保留该层信息，供 UI 复用。
- 前端工作台与简化插画页都暴露这一组输入。

## 验证

- `python -m unittest tests.smoke.test_prompt_packs -q`
- `python -m unittest tests.smoke.test_illustration_command -q`
- `python -m unittest discover -s tests`
- `npm --prefix ui run build`

## 风险

- 中文 pack id 会影响 pack name 解析与默认值匹配，需补 smoke test。
- 文本设计层如果做成模板专属字段，容易与 use-case 形成平行维度；本轮改为请求级正交参数，降低结构耦合。
- 需要避免把“文字设计”误做成强制项，必须保证默认纯绘图行为不变。
