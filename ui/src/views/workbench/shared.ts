import type { ProjectOption } from "@/api/storyCanvas";

export type TreeDragKind = "chapter" | "entity";

export function buildProjectOptionLabel(item: ProjectOption): string {
  const sourceLabel = item.source === "recent" ? "最近" : "项目";
  return item.genre ? `${item.title} · ${item.genre} · ${sourceLabel}` : `${item.title} · ${sourceLabel}`;
}

export function syncTreeOrder(current: string[], latest: string[]): string[] {
  const latestSet = new Set(latest);
  const kept = current.filter((item) => latestSet.has(item));
  const keptSet = new Set(kept);
  const appended = latest.filter((item) => !keptSet.has(item));
  return [...kept, ...appended];
}

export function moveTreeItem(ids: string[], draggedId: string, targetId: string): string[] {
  const next = [...ids];
  const fromIndex = next.indexOf(draggedId);
  const toIndex = next.indexOf(targetId);
  if (fromIndex < 0 || toIndex < 0) {
    return ids;
  }
  next.splice(fromIndex, 1);
  next.splice(toIndex, 0, draggedId);
  return next;
}

export function applyTreeOrder<T extends { id: string }>(items: T[], orderIds: string[]): T[] {
  const lookup = new Map(items.map((item) => [item.id, item]));
  const ordered = orderIds.map((id) => lookup.get(id)).filter((item): item is T => Boolean(item));
  const seen = new Set(ordered.map((item) => item.id));
  const extra = items.filter((item) => !seen.has(item.id));
  return [...ordered, ...extra];
}
