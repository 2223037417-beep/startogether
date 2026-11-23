import { withBase } from "vitepress";
import { onMounted, onUnmounted, ref } from "vue";
import data from "../../.generated/journal.json";
export { data };
export const diary = (e) =>
  withBase("/entries/" + e.user + "/" + e.date + ".html");
export const profileUrl = (user) =>
  withBase("/profile.html?user=" + encodeURIComponent(user));
export const emptyStats = { total: 0, run: 0, longest: 0, last: "" };
export function useToday() {
  const today = ref(data.today);
  let timer;
  onMounted(() => {
    function refresh() {
      today.value = new Date(Date.now() + 28800000).toISOString().slice(0, 10);
    }
    refresh();
    timer = setInterval(refresh, 60000);
  });
  onUnmounted(() => clearInterval(timer));
  return today;
}
