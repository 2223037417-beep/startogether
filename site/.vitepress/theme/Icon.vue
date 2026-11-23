<script setup>
defineProps({ name: String });
const paths = {
  pen: "M13.5 6.5l4 4M4 20l4.5-1 12-12a2.8 2.8 0 0 0-4-4l-12 12L4 20Z",
  book: "M3 5c4-1 6 0 9 2 3-2 5-3 9-2v14c-4-1-6 0-9 2-3-2-5-3-9-2ZM12 7v14",
  calendar: "M4 6h16v15H4zM8 3v6m8-6v6M4 11h16m-12 4h1m3 0h1m3 0h1",
  leaf: "M19 4C8 3 4 8 6 15c4 5 12 2 13-11ZM4 21c2-6 6-10 11-13",
  search: "M20 20l-5-5m2-5a7 7 0 1 1-14 0 7 7 0 0 1 14 0",
  link: "M14 4h6v6m0-6-10 10m0-8H4v14h14v-6",
};
</script>
<template>
  <svg
    aria-hidden="true"
    width="19"
    height="19"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.65"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <path :d="paths[name]" />
  </svg>
</template>
