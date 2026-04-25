# ADR-002: Optional Dependencies and Providers Boundary

> 状态: 已接受
> 日期: 2026-04-25

## 1. 背景

项目当前以 stdlib-only 为基线，核心 CLI 闭环已经验证可用。但 v3 计划新增的 style analysis、卷级审阅增强和 illustration provider 接入，存在三类明显的重复实现风险：

- 高重复实现成本的文本近似/聚类类算法
- 持续膨胀的类型词表、视觉词典和平台风格词表
- 与外部图像或模型服务耦合的 provider / prompt 逻辑

如果继续把这些能力全部做成仓库内硬编码实现，会造成：

- `utils/text.py` 和 service 模块持续膨胀
- 外部 API 调用和纯业务逻辑混放
- 为了保持零依赖而重复实现低价值算法

## 2. 决策

仓库正式采用以下依赖与扩展边界：

1. **Base install 保持零外部依赖**
   - 核心 CLI、状态协议、基础 heuristics、离线 smoke test 必须在 stdlib-only 下可运行

2. **允许 optional dependencies**
   - 第三方库只能作为可选增强能力引入
   - 通过 `pyproject.toml` 的 optional dependencies / extras 管理
   - 缺失 optional dependency 时必须降级，而不是让核心命令直接失败

3. **允许外部资源包（packs）**
   - 词表、字典、prompt pack、workflow review profile 不必全部内置在仓库代码中
   - 必须保留 builtin 最小集，确保离线可用和回归稳定

4. **引入 `providers/` 作为 side-effecting client 的 canonical owner**
   - 外部 API 调用、SDK 封装、网络鉴权、可选重型库包装统一放在 `src/story_harness_cli/providers/`
   - `services/` 保持纯业务逻辑，不直接执行网络调用或依赖特定 provider SDK

## 3. 依赖分层

| 层级 | 说明 | 例子 |
|------|------|------|
| Base | stdlib-only 核心运行基线 | argparse、json、urllib.request、builtin heuristics |
| Extras | 可选第三方增强能力 | `rapidfuzz`、未来的 provider SDK |
| Packs | 代码外可替换资源 | style lexicon、illustration prompt pack、workflow review profile |
| Providers | 外部系统和可选依赖适配层 | OpenAI image client、local similarity wrapper |

## 4. 结果与约束

### 正面影响

- 核心 CLI 仍保留零依赖和离线可运行特性
- 可以避免在仓库内持续重复实现低价值算法
- provider / SDK 边界更清晰，服务层纯度不被破坏
- 词表和 prompt 可以按 pack 演进，不必持续堆积到单一模块

### 负面影响

- 需要维护 builtin fallback、extras 和 packs 三套口径
- 需要补充依赖缺失时的降级和测试策略
- 文档和实现必须明确记录结果来源（builtin / extra / provider / pack）

## 5. 落地要求

- 所有新增 optional dependency 都必须满足：
  - 不影响 base install
  - 不改变状态文件格式的核心语义
  - 有明确的缺失依赖降级路径
  - 有离线测试或 mock provider 测试
- `services/` 只能：
  - 构造请求 payload
  - 执行 builtin fallback
  - 解释 provider 返回结果
- `providers/` 可以：
  - 调用外部 API
  - 包装 optional dependency
  - 返回标准化结果结构
- `commands/` 负责：
  - 参数解析
  - 文件 I/O
  - 选择 builtin / pack / provider 路径

## 6. 首批适用范围

- Style analysis:
  - builtin heuristic 继续保留
  - 允许引入轻量 optional dependency 处理文本近似匹配
- Illustration:
  - 优先使用 stdlib HTTP client 接入 OpenAI image API
  - 若未来 provider 增多或维护成本上升，可再把官方 SDK 作为 optional dependency
- Workflow review:
  - 允许 review profile / prompt pack 外部化
  - gate 判定必须保留 builtin fallback

## 7. 被放弃的备选方案

### 备选方案 A: 继续坚持全仓库严格 stdlib-only

- 为什么没选:
  - 会把本可复用的算法、词表和 prompt 维护成本全部压回仓库内部
  - 不利于 v3 的 style / illustration 能力扩展

### 备选方案 B: 直接改成默认依赖外部 SDK 和算法库

- 为什么没选:
  - 会破坏当前离线可运行和最小安装基线
  - 会让核心 CLI 与网络环境、安装环境强绑定

### 备选方案 C: 不设 `providers/`，继续把 adapter 写进 `services/`

- 为什么没选:
  - 会破坏服务层无副作用边界
  - 会让外部 API 调用和纯业务逻辑耦合

## 8. 迁移或落地要求

- `docs/ARCHITECTURE_GUARDRAILS.md` 需同步更新依赖与目录边界
- `docs/v3-plan.md` 需改为以本 ADR 为正式依赖策略
- `docs/PROJECT_PROFILE.md` 需更新为“base install 零依赖 + optional extras”口径

## 9. 何时需要重新审查

- 需要把某个第三方库升级为 base install 默认依赖时
- `providers/` 边界无法覆盖新的外部系统接入需求时
- 状态协议开始与 provider / SDK 强绑定时
