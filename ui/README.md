# Story Canvas UI

`ui/` 是 `Story Canvas` 的早期视觉壳，当前使用：

- `Vue 3`
- `Vite`
- `TDesign Vue Next`

当前骨架包含：

- 项目概览页
- 章节与审查面板
- 插画工作台面板

本地开发：

```powershell
cd ui
npm install
npm run dev
```

默认开发地址：

```text
http://127.0.0.1:43187/
```

生产构建：

```powershell
cd ui
npm run build
```

当前阶段说明：

- 主命令入口为 `story-canvas`，旧命令 `story-harness` 仍保留兼容
- UI 只作为文件协议和 provider 能力的视觉壳，不引入新的真相源

