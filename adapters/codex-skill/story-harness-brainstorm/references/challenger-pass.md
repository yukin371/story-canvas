# Challenger Pass

当宿主支持 subagent / fresh thread，且主线程想在收束前做一次独立挑战时，再读取本文件。

用最小上下文挑战当前领先方向。

## 输入边界

只给 challenger：

1. 当前火种
2. 当前领先方向摘要
3. 如有必要，再给一个备选方向摘要

保持输入简洁：

1. 不传主线程完整推理过程
2. 不传预设结论
3. 不传希望 challenger 复述的答案

## Challenger Task

只让 challenger 做三件事：

1. 指出当前领先方向最大的一个结构弱点
2. 提一个更强备选，或说明为什么没有更强备选
3. 给出是否值得推翻当前领先方向的结论

## 推荐输出格式

```text
Lead direction weakness:
Better alternative:
Override verdict:
Reason:
```

## 主线程怎么用

主线程收到 challenger 输出后，只做：

1. 判断这个弱点是否真实
2. 判断是否需要切换方向
3. 若不切换，说明为什么当前方向仍更优

把 challenger 输出压成一条明确判断，再回主线程做取舍。
