# GUI Polish Design

**Goal:** Make the PyQt stitching tool feel like a calm professional desktop utility for image/forensics workflows.

**Direction:** Use a restrained "professional forensic tool" style: a dark title band, a clean light workspace, clear parameter grouping, a strong primary action, and a structured terminal-like log panel.

**Scope:**
- Keep the existing workflow and defaults.
- Improve spacing, typography, colors, labels, and control states.
- Add a folder status area and a compact run summary.
- Extract reusable style helpers so visual polish is not mixed into solver logic.

**Non-goals:**
- No algorithm changes.
- No new image previewer in this pass.
- No decorative illustration or landing-page treatment.
