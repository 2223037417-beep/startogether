<script setup>
import { useData, withBase } from "vitepress";
import Calendar from "./Calendar.vue";
import Icon from "./Icon.vue";
import { data } from "./shared";
const { theme } = useData();
</script>
<template>
  <main class="shell home">
    <section class="hero">
      <div class="hero-text">
        <p class="signature"><i></i> 星起偕行</p>
        <h1>把微小的进步，<br /><em>写成日常。</em></h1>
        <p class="intro">
          让进步 看得见<br />用一篇篇 Markdown
          日记，和大家一起成长。
        </p>
        <div class="actions">
          <a class="button primary" :href="withBase('/guide/')"
            ><Icon name="pen" />开始记录</a
          ><a class="button secondary" :href="withBase('/letter.html')"
            ><Icon name="book" />了解项目</a
          >
        </div>
      </div>
      <figure class="hero-scene">
        <div class="hero-landscape" aria-hidden="true">
          <img class="day-scene" :src="withBase('/woodland.webp')" alt="" />
          <img class="night-scene" :src="withBase('/perseids.jpg')" alt="" />
        </div>
        <figcaption class="night-credit">
          <a href="https://www.nasa.gov/image-article/behold-perseid-meteor-shower/">
            英仙座流星雨 · NASA / Bill Ingalls
          </a>
        </figcaption>
      </figure>
    </section>
    <Calendar :entries="data.entries" :stats="data.community" home />
    <section id="about" class="about">
      <span class="symbol"><Icon name="leaf" /></span>
      <div>
        <h2>关于 Startogether</h2>
        <p>
          一件做成的小事，一次坚持下来的练习，都值得留下一笔。每人每天一篇日记，写给自己，也让同行的人读到。
        </p>
        <a
          class="text-link"
          :href="
            theme.repository ||
            'https://github.com/search?q=startogether+in%3Aname&type=repositories'
          "
          >{{ theme.repository ? "查看 GitHub 仓库" : "在 GitHub 查找仓库" }}
          <Icon name="link"
        /></a>
      </div>
    </section>
  </main>
</template>
