# Providers 模块说明

> 最后更新: 2026-04-30
> 状态: 当前有效模块文档

## 1. 模块职责

- 封装外部 API、SDK 和 optional dependency wrapper
- 为 commands 层提供统一的 provider 装载入口
- 隔离 provider 特定错误和依赖缺失错误

## 2. Owns

- optional dependency 加载 helper
- provider registry
- image / similarity 等外部能力 wrapper
- OpenAI image HTTP client 这类最小 provider 骨架
- OpenAI-compatible text HTTP client 这类最小 provider 骨架
- sentence-transformers embedding wrapper 与 builtin fallback
- OpenAI image edits multipart 组装与上传
- OpenAI image response 的 artifact 归一化与字节提取
- 多图返回结果的统一 materialize 语义
- 文本 provider request 构造与 provider response 文本抽取

## 3. Must Not Own

- 项目状态持久化
- 业务规则判定
- argparse 参数解析
- JSON 输出格式化

## 4. 不变量

- 缺失 optional dependency 时，必须给出可解释错误或返回可降级信号
- provider 返回结构应尽量标准化，避免把 SDK 特定结构泄露到 commands / services
- 不直接写项目状态文件
- 不把 model id 枚举硬编码为单一固定值，优先接受 commands 传入的配置值
- binary upload / multipart 细节必须收敛在 provider 内，不向 commands 泄露 HTTP 组装逻辑
- 文本 provider 不拥有 review 评分规则，只返回标准化文本结果供 command / service 解析

## 5. 文档同步触发条件

- 新增或删除 provider capability
- provider registry 结构变化
- optional dependency 策略变化
