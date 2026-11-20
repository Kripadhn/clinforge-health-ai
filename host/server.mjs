// Thin chat host: serves the UI and proxies POST /chat to the agent, forwarding the bearer token.
import http from "node:http";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const dir = dirname(fileURLToPath(import.meta.url));
const AGENT = process.env.AGENT_URL || "http://localhost:8003";
const PORT = Number(process.env.PORT || 5173);
const APPS = join(dir, "..", "apps");
const files = {
  "/": [join(dir, "index.html"), "text/html"],
  "/host.js": [join(dir, "host.js"), "text/javascript"],
  "/views.html": [join(APPS, "views.html"), "text/html"],
  "/views.js": [join(APPS, "views.js"), "text/javascript"],
};

http.createServer(async (req, res) => {
  if (req.method === "GET" && req.url.startsWith("/views/")) {
    // data proxy for the apps views; bearer token forwarded, scope enforced by the MCP server
    try {
      const r = await fetch(AGENT + req.url, { headers: { Authorization: req.headers.authorization || "" } });
      res.writeHead(r.status, { "Content-Type": "application/json" });
      res.end(await r.text());
    } catch (e) {
      res.writeHead(502, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ detail: "agent unreachable" }));
    }
    return;
  }
  if (req.method === "POST" && req.url === "/chat") {
    const chunks = [];
    for await (const c of req) chunks.push(c);
    try {
      const r = await fetch(AGENT + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: req.headers.authorization || "" },
        body: Buffer.concat(chunks),
      });
      res.writeHead(r.status, { "Content-Type": "application/json" });
      res.end(await r.text());
    } catch (e) {
      res.writeHead(502, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ detail: "agent unreachable" }));
    }
    return;
  }
  const f = files[req.url];
  if (!f) { res.writeHead(404); res.end("not found"); return; }
  res.writeHead(200, { "Content-Type": f[1] });
  res.end(await readFile(f[0]));
}).listen(PORT, () => console.log("host on http://localhost:" + PORT));
