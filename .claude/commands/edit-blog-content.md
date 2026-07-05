---
description: Edit an existing post's prose (de-slop / zinsser / tighten) via the safe dump -> dry-run -> load workflow
argument-hint: <what to do, e.g. "de-slop my latest TIL and save it">
---

Use the **edit-blog-content** skill (`.claude/skills/edit-blog-content/SKILL.md`) to handle this request:

$ARGUMENTS

Follow the skill's workflow exactly — no shortcuts:

1. `dump_content` to export the target entry's markdown field(s) to files.
2. Run the requested prose skill (de-slopper, zinsser, analyze-prose, ...) on the dumped file, editing only the body below the front-matter.
3. `load_content --dry-run` as the accept gate: show the diff and confirm before writing.
4. `load_content` to write the accepted change back through the Django ORM.

Never use raw SQL or the admin form to change content. Work local-first; promote to production only if explicitly asked.
