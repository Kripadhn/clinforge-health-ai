const log = document.getElementById("log");

function add(cls, text, meta) {
  const d = document.createElement("div");
  d.className = cls;
  d.textContent = text;
  if (meta) {
    const m = document.createElement("div");
    m.className = "meta";
    m.textContent = meta;
    d.appendChild(m);
  }
  log.appendChild(d);
  d.scrollIntoView();
}

document.getElementById("f").addEventListener("submit", async (e) => {
  e.preventDefault();
  const box = document.getElementById("msg");
  const message = box.value.trim();
  if (!message) return;
  box.value = "";
  add("user", message);
  const r = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + document.getElementById("tok").value },
    body: JSON.stringify({ message }),
  });
  const body = await r.json();
  if (!r.ok) return add("bot", "Error " + r.status + ": " + (body.detail || "request failed"));
  const tools = body.tool_calls.map((c) => c.tool + (c.ok ? "" : " (denied)")).join(", ");
  add("bot", body.answer, "model: " + body.model + " | tools: " + tools);
});
