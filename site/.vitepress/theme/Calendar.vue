<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { withBase } from "vitepress";
import Icon from "./Icon.vue";
import { diary, useToday } from "./shared";
const props = defineProps({ entries: Array, stats: Object, home: Boolean });
const today = useToday();
const currentYear = computed(() => Number(today.value.slice(0, 4)));
const year = ref(currentYear.value);
const selected = ref("");
const scroller = ref(null);
function showToday() {
  const box = scroller.value;
  const cell = box?.querySelector(".today");
  if (box && box.scrollWidth > box.clientWidth) {
    box.scrollLeft = cell ? cell.offsetLeft - box.clientWidth * 0.65 : 0;
  }
}
onMounted(showToday);
watch(currentYear, (value, old) => {
  if (year.value === old) year.value = value;
});
watch(year, () => nextTick(showToday));
const years = computed(() =>
  [
    ...new Set([
      currentYear.value,
      currentYear.value - 1,
      year.value,
      ...props.entries.map((e) => +e.date.slice(0, 4)),
    ]),
  ].sort((a, b) => b - a),
);
const byDate = computed(() => {
  const result = new Map();
  for (const e of props.entries) {
    if (!result.has(e.date)) result.set(e.date, []);
    result.get(e.date).push(e);
  }
  return result;
});
watch([year, () => props.entries], () => (selected.value = ""));
const cells = computed(() => {
  const start = Date.UTC(year.value, 0, 1),
    end = Date.UTC(year.value + 1, 0, 1);
  const offset = (new Date(start).getUTCDay() + 6) % 7;
  const result = [];
  for (let ms = start, i = offset; ms < end; ms += 86400000, i++) {
    const date = new Date(ms).toISOString().slice(0, 10);
    const items = byDate.value.get(date) || [];
    const singleDiary = items.length === 1 && !items[0].checkInOnly;
    const label =
      date +
      " · " +
      (items.length
        ? items.length === 1 && items[0].checkInOnly ? "已打卡 · 正文未分享" : items.length + " 人打卡"
        : date > today.value
          ? "尚未到来"
          : "未记录");
    result.push({
      date,
      items,
      singleDiary,
      label,
      col: Math.floor(i / 7) + 1,
      row: (i % 7) + 2,
    });
  }
  return result;
});
const months = computed(() =>
  cells.value.filter((c) => c.date.endsWith("-01")),
);
const streak = computed(() =>
  Date.parse(today.value) - Date.parse(props.stats.last) <= 86400000
    ? props.stats.run
    : 0,
);
</script>
<template>
  <section class="calendar-panel" aria-label="年度成长日历">
    <header class="cal-head">
      <div class="cal-heading">
        <span class="symbol"><Icon name="calendar" /></span>
        <div>
          <h2>{{ home ? "成长日历" : "年度记录" }}</h2>
          <p>
            {{
              home
                ? "每一格，都是可以记录的一天。"
                : "选择已点亮的日期，查看当天的记录。"
            }}
          </p>
        </div>
      </div>
      <label class="year"
        ><select v-model.number="year" aria-label="查看年份">
          <option v-for="y in years" :key="y" :value="y">{{ y }} 年</option>
        </select></label
      >
    </header>
    <div
      ref="scroller"
      class="scroll-grid"
      tabindex="0"
      aria-label="日历，可横向滚动"
    >
      <div class="heat-wrap">
        <div class="week">
          <span
            v-for="(d, i) in ['', '一', '', '三', '', '五', '', '日']"
            :key="i"
            >{{ d }}</span
          >
        </div>
        <div class="heat" :style="{ '--cols': cells.at(-1).col }">
          <span
            v-for="m in months"
            :key="m.date"
            class="month"
            :style="{ gridColumn: m.col, gridRow: 1 }"
            >{{ Number(m.date.slice(5, 7)) }}月</span
          >
          <component
            v-for="c in cells"
            :key="c.date"
            :is="
              c.singleDiary ? 'a' : c.items.length ? 'button' : 'span'
            "
            class="day"
            :class="{
              recorded: c.items.length,
              today: c.date === today,
              future: c.date > today,
            }"
            :style="{ gridColumn: c.col, gridRow: c.row }"
            :title="c.label"
            :aria-label="c.label"
            :href="c.singleDiary ? diary(c.items[0]) : undefined"
            @click="selected = c.items.length && !c.singleDiary ? c.date : ''"
          ></component>
        </div>
      </div>
    </div>
    <div class="cal-foot">
      <span>{{
        stats.total
          ? "累计记录 " + stats.total + " 天"
          : "第一次打卡后，日历就会亮起。"
      }}</span>
      <div class="legend">
        <span><b></b>未记录</span><span><b class="active"></b>已记录</span
        ><span><b class="now"></b>今天</span>
      </div>
    </div>
    <div v-if="selected" class="selections">
      <b>{{ selected }}</b>
      <template v-for="e in byDate.get(selected)" :key="e.user">
        <span v-if="e.checkInOnly">@{{ e.user }} 已打卡 · 正文未分享</span>
        <a v-else :href="diary(e)">@{{ e.user }} 的日记</a>
      </template>
    </div>
    <div v-if="!home" class="metrics">
      <div
        v-for="item in [
          [stats.total, '累计打卡'],
          [streak, '当前连续'],
          [stats.longest, '最长连续'],
        ]"
        :key="item[1]"
      >
        <strong>{{ item[0] }}<small> 天</small></strong
        ><span>{{ item[1] }}</span>
      </div>
    </div>
  </section>
</template>
