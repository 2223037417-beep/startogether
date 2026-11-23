import { defineConfig } from "vitepress";
import { base, repository } from "../settings.mjs";
export default defineConfig({
  base,
  title: "Startogether",
  lang: "zh-CN",
  description: "用一篇日记，记录每天的小成功。",
  appearance: true,
  lastUpdated: false,
  head: [["link", { rel: "icon", href: base + "mark.svg" }]],
  themeConfig: {
    repository,
    logo: "/mark.svg",
    siteTitle: "Startogether",
    nav: [
      { text: "首页", link: "/" },
      { text: "成长日历", link: "/calendar" },
      { text: "个人主页", link: "/profile" },
      { text: "参与指南", link: "/guide/" },
    ],
    sidebar: {
      "/guide/": [
        {
          text: "参与指南",
          items: [
            { text: "开始记录", link: "/guide/" },
            { text: "提交与合并", link: "/guide/submit" },
            { text: "常见问题", link: "/guide/faq" },
          ],
        },
      ],
    },
    outline: { label: "本页目录" },
    docFooter: { prev: "上一篇", next: "下一篇" },
    sidebarMenuLabel: "指南目录",
    returnToTopLabel: "回到顶部",
    darkModeSwitchLabel: "外观",
    lightModeSwitchTitle: "切换到浅色",
    darkModeSwitchTitle: "切换到深色",
    socialLinks: repository ? [{ icon: "github", link: repository }] : [],
  },
});
