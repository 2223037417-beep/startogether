import DefaultTheme from "vitepress/theme";
import Home from "./Home.vue";
import Archive from "./Archive.vue";
import Reader from "./Reader.vue";
import "./style.css";
export default {
  ...DefaultTheme,
  enhanceApp(ctx) {
    DefaultTheme.enhanceApp?.(ctx);
    for (const [name, component] of Object.entries({ Home, Archive, Reader }))
      ctx.app.component(name, component);
  },
};
