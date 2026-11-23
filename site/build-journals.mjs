// Diary prose is untrusted: render plain Markdown outside VitePress's Vue compiler.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import MarkdownIt from "markdown-it";
import tasks from "markdown-it-task-lists";
import { repository } from "./settings.mjs";

const site = path.dirname(fileURLToPath(import.meta.url));
const journal = path.resolve(site, "../journal");
const output = path.join(site, "entries");
const generated = path.join(site, ".generated");
fs.rmSync(output, { recursive: true, force: true });
fs.mkdirSync(generated, { recursive: true });
const markdown = new MarkdownIt({ html: false }).use(tasks);
// Relative links and images retain the directory of the original Markdown file.
for (const [rule, attribute, raw] of [
  ["link_open", "href", false],
  ["image", "src", true],
]) {
  const original = markdown.renderer.rules[rule];
  markdown.renderer.rules[rule] = (tokens, index, options, env, renderer) => {
    const token = tokens[index];
    const value = token.attrGet(attribute);
    if (repository && value && !/^(?:[a-z][a-z0-9+.-]*:|[/#])/i.test(value)) {
      const root = raw
        ? repository.replace("github.com", "raw.githubusercontent.com") +
          "/main/"
        : repository + "/blob/main/";
      token.attrSet(
        attribute,
        new URL(value, root + "journal/" + env.relative).href,
      );
    }
    return original
      ? original(tokens, index, options, env, renderer)
      : renderer.renderToken(tokens, index, options);
  };
}
const entries = [];
function scan(directory) {
  for (const file of fs.readdirSync(directory, { withFileTypes: true })) {
    const full = path.join(directory, file.name);
    if (file.isDirectory()) {
      scan(full);
      continue;
    }
    const relative = path.relative(journal, full).split(path.sep).join("/");
    const found = relative.match(
      /^(\d\d)\/(\d\d)\/(\d\d)\/([a-z0-9]+(?:-[a-z0-9]+)*)\.md$/,
    );
    if (!found || !file.isFile()) throw new Error("非法日记路径 " + relative);
    const [, y, m, d, user] = found;
    const date = "20" + y + "-" + m + "-" + d;
    if (
      new Date(date + "T00:00:00Z").toISOString().slice(0, 10) !== date ||
      user.length > 39
    )
      throw new Error(relative);
    const source = fs.readFileSync(full, "utf8");
    const html = markdown.render(source, { relative });
    const dest = path.join(output, user);
    fs.mkdirSync(dest, { recursive: true });
    fs.writeFileSync(
      path.join(dest, date + ".json"),
      JSON.stringify({ html, date, user, relative }),
    );
    fs.writeFileSync(
      path.join(dest, date + ".md"),
      `---\nlayout: page\ntitle: "${date} · @${user}"\n---\n<script setup>\nimport entry from './${date}.json'\n</script>\n<Reader :entry="entry" />\n`,
    );
    entries.push({ date, user });
  }
}
if (fs.existsSync(journal)) scan(journal);
entries.sort(
  (a, b) => b.date.localeCompare(a.date) || a.user.localeCompare(b.user),
);
function summarize(records) {
  const dates = [...new Set(records.map((e) => e.date))].sort();
  let run = 0,
    longest = 0,
    previous = 0;
  for (const date of dates) {
    const next = Date.parse(date);
    run = next - previous === 86400000 ? run + 1 : 1;
    longest = Math.max(longest, run);
    previous = next;
  }
  return { total: dates.length, last: dates.at(-1) || "", run, longest };
}
const users = new Map();
for (const entry of entries) {
  if (!users.has(entry.user)) users.set(entry.user, []);
  users.get(entry.user).push(entry);
}
fs.writeFileSync(
  path.join(generated, "journal.json"),
  JSON.stringify({
    entries,
    community: summarize(entries),
    people: Object.fromEntries(
      [...users].map(([user, records]) => [user, summarize(records)]),
    ),
    today: new Date(Date.now() + 8 * 3600000).toISOString().slice(0, 10),
  }),
);
console.log(`读取 ${entries.length} 篇日记，${users.size} 位记录者。`);
