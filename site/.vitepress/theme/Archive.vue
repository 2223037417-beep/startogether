<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, withBase } from "vitepress";
import { data, diary, emptyStats, profileUrl } from "./shared";
import Icon from "./Icon.vue";
import Calendar from "./Calendar.vue";
const props = defineProps({ profile: Boolean });
const route = useRoute(),
  query = ref(""),
  user = ref(""),
  limit = ref(25),
  error = ref("");
const people = Object.keys(data.people).sort();
const records = computed(() =>
  user.value
    ? data.entries.filter((e) => e.user === user.value)
    : props.profile
      ? []
      : data.entries,
);
const stats = computed(() =>
  user.value
    ? Object.hasOwn(data.people, user.value)
      ? data.people[user.value]
      : emptyStats
    : props.profile
      ? emptyStats
      : data.community,
);
function load() {
  const value = new URLSearchParams(location.search).get("user") || "";
  user.value = valid(value) ? value.toLowerCase() : "";
  query.value = user.value;
  limit.value = 25;
}
function valid(value) {
  return value.length <= 39 && /^[a-z0-9]+(?:-[a-z0-9]+)*$/i.test(value);
}
function search() {
  const value = query.value.trim().toLowerCase();
  if (value && !valid(value)) {
    error.value = "请输入有效的 GitHub 用户名。";
    return;
  }
  error.value = "";
  const url = new URL(location.href);
  if (value) url.searchParams.set("user", value);
  else url.searchParams.delete("user");
  location.assign(url.href);
}
onMounted(load);
watch(
  () => route.path,
  () => {
    if (typeof window !== "undefined") load();
  },
);
</script>
<template>
  <main class="shell archive">
    <header class="archive-head">
      <img
        v-if="profile && user"
        class="avatar"
        :src="'https://github.com/' + user + '.png?size=128'"
        alt=""
        @error="$event.target.style.visibility = 'hidden'"
      />
      <div>
        <h1>{{ profile ? (user ? "@" + user : "个人主页") : "成长日历" }}</h1>
        <p v-if="!profile">
          按年份回顾{{ user ? " @" + user : "所有参与者" }}的成长记录。
        </p>
        <p v-else-if="!user">输入 GitHub 用户名，打开个人成长档案。</p>
        <a v-else class="text-link" :href="'https://github.com/' + user"
          >GitHub 主页 <Icon name="link"
        /></a>
      </div>
    </header>
    <form class="search" @submit.prevent="search">
      <label for="login">GitHub 用户名</label>
      <div>
        <Icon name="search" /><input
          id="login"
          v-model="query"
          list="participants"
          placeholder="输入用户名"
          autocomplete="off"
        /><datalist id="participants">
          <option v-for="p in people" :key="p">{{ p }}</option></datalist
        ><button class="primary button">查看</button>
      </div>
      <p v-if="error" role="alert">{{ error }}</p>
    </form>
    <template v-if="!profile || user"
      ><Calendar :entries="records" :stats="stats" />
      <section class="history">
        <h2>
          历史记录 <small>{{ records.length }} 条</small>
        </h2>
        <p v-if="!records.length">
          这里还没有打卡记录。<a class="text-link" :href="withBase('/guide/')"
            >写下第一篇</a
          >
        </p>
        <div
          v-for="e in records.slice(0, limit)"
          :key="e.date + e.user"
          class="entry-row"
        >
          <span v-if="e.checkInOnly">{{ e.date }} 已打卡 · 正文未分享</span>
          <a v-else :href="diary(e)"><Icon name="book" /> {{ e.date }} 的日记</a
          ><a :href="profileUrl(e.user)">@{{ e.user }}</a>
        </div>
        <button
          v-if="limit < records.length"
          class="button secondary"
          @click="limit += 25"
        >
          显示更多
        </button>
      </section></template
    >
    <section v-else class="history">
      <h2>记录者</h2>
      <p v-if="!people.length">首次打卡合并后，记录者会出现在这里。</p>
      <a v-for="p in people" :key="p" class="participant" :href="profileUrl(p)"
        >@{{ p }}</a
      >
    </section>
  </main>
</template>
