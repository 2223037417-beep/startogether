import { execFileSync } from "node:child_process";

function originSlug() {
  try {
    const remote = execFileSync("git", ["remote", "get-url", "origin"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
    return remote.match(/github\.com[:/]([\w.-]+\/[\w.-]+?)(?:\.git)?$/i)?.[1];
  } catch {
    return "";
  }
}
const slug = process.env.GITHUB_REPOSITORY || originSlug();
export const repository = slug ? "https://github.com/" + slug : "";
export const base =
  process.env.SITE_BASE ?? "/" + (slug?.split("/")[1] || "startogether") + "/";
