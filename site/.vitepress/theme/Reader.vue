<script setup>
import { useData } from "vitepress";
import { profileUrl } from "./shared";
import Icon from "./Icon.vue";
defineProps({ entry: Object });
const { theme } = useData();
</script>
<template>
  <main class="reader">
    <header>
      <p class="signature"><i></i> 成长日记</p>
      <h1>{{ entry.date }}</h1>
      <a class="text-link" :href="profileUrl(entry.user)"
        >@{{ entry.user }} 的主页</a
      >
    </header>
    <article class="vp-doc prose" v-html="entry.html"></article>
    <footer>
      <a :href="profileUrl(entry.user)">返回个人主页</a
      ><a
        v-if="theme.repository"
        :href="theme.repository + '/blob/main/journal/' + entry.relative"
        >GitHub 原文 <Icon name="link"
      /></a>
    </footer>
  </main>
</template>
