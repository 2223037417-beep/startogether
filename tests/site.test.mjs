import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

test("静态日历去重、跨年连续天数和日记正文渲染", (t) => {
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "startogether-test-"));
  t.after(() => fs.rmSync(temp, { recursive: true, force: true }));
  const site = path.join(temp, "site");
  fs.mkdirSync(site);
  fs.symlinkSync(
    path.join(root, "node_modules"),
    path.join(temp, "node_modules"),
    "junction",
  );
  for (const name of ["settings.mjs", "build-journals.mjs"])
    fs.copyFileSync(path.join(root, "site", name), path.join(site, name));
  function build() {
    execFileSync(process.execPath, [path.join(site, "build-journals.mjs")], {
      cwd: temp,
      env: { ...process.env, GITHUB_REPOSITORY: "fixtures/journals" },
    });
    return JSON.parse(
      fs.readFileSync(path.join(site, ".generated/journal.json"), "utf8"),
    );
  }
  assert.deepEqual(build().entries, []);
  for (const file of [
    "25/12/30/alice.md",
    "25/12/31/alice.md",
    "26/01/01/alice.md",
    "26/01/03/alice.md",
    "26/01/03/bob.md",
  ]) {
    const full = path.join(temp, "journal", file);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(
      full,
      "# 记录\n\n- [x] 完成\n\n<aside>原文</aside>\n\n{{ 今日 }}\n\n[相关日记](alice.md)",
    );
  }
  const marker = path.join(temp, "journal/25/12/31/alice.md");
  fs.writeFileSync(marker, "");
  const data = build();
  const record = data.entries.find(e => e.date === "2025-12-31");
  assert.equal(record.checkInOnly, true);
  const privatePage = path.join(site, "entries/alice/2025-12-31");
  assert.ok(!fs.existsSync(privatePage + ".md"));
  assert.ok(!fs.existsSync(privatePage + ".json"));
  fs.writeFileSync(marker, "I chose to share this");
  const shared = build();
  assert.deepEqual(shared.people.alice, data.people.alice);
  assert.equal(shared.entries.find(e => e.date === record.date).checkInOnly, false);
  assert.match(JSON.parse(fs.readFileSync(privatePage + ".json")).html, /chose to share/);
  assert.equal(data.entries.length, 5);
  assert.deepEqual(data.community, {
    total: 4,
    last: "2026-01-03",
    run: 1,
    longest: 3,
  });
  assert.deepEqual(data.people.alice, data.community);
  assert.equal(data.people.bob.total, 1);
  assert.equal(data.entries[0].date, "2026-01-03");
  const output = path.join(site, "entries/alice/2026-01-03");
  const { html } = JSON.parse(fs.readFileSync(output + ".json"));
  assert.match(html, /type="checkbox"/);
  assert.match(html, /&lt;aside&gt;/);
  assert.match(
    html,
    /https:\/\/github.com\/fixtures\/journals\/blob\/main\/journal\/26\/01\/03\/alice.md/,
  );
  assert.ok(!fs.readFileSync(output + ".md", "utf8").includes("{{ 今日 }}"));
});
