# Clinical views

Finpilot-AI ships a transactions table and a spending chart; the ClinForge equivalents live here:

- **Lab trend** - single-series line chart for any observation code (search by name, e.g. "Hemoglobin A1c"),
  with crosshair tooltip, direct-labeled last value, and a table view.
- **Encounter timeline** - one labeled swimlane per encounter class, one dot per encounter, hover tooltip,
  and a table view.

Open http://localhost:5173/views.html (served by the host). Data flows host -> agent `/views/*` -> MCP tools,
so patient scope is enforced by the MCP server exactly as in chat. Light/dark theming and the categorical
palette follow a validated accessible palette; identity is never carried by color alone (labeled rows + tables).
