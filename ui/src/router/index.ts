import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "dashboard",
      component: () => import("@/views/DashboardView.vue"),
      meta: { title: "概览" },
    },
    {
      path: "/chapters",
      name: "chapters",
      component: () => import("@/views/ChaptersView.vue"),
      meta: { title: "章节与审查" },
    },
    {
      path: "/illustration",
      name: "illustration",
      component: () => import("@/views/IllustrationView.vue"),
      meta: { title: "插画工作台" },
    },
  ],
});

router.afterEach(() => {
  document.title = "Story Canvas - 工作台";
});

export default router;
