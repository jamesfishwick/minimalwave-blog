---
name: edit-blog-content
description: Run prose/markdown skills (de-slopper, zinsser, analyze-prose, etc.) against this blog's content and write accepted edits back to the database. Use when the user wants to clean up, rewrite, or improve the markdown body/summary of an Entry, Blogmark, TIL, or Project — e.g. "run the de-slopper on my latest post", "zinsser this entry", "tighten the prose on <slug> and save it". Content lives in Postgres, not files, so this skill exports it to files, edits there, shows a diff for acceptance, then writes back through the Django ORM.
---

# Edit blog content

This blog's content is **markdown stored in Postgres columns** (`Entry.body/summary`, `Blogmark.commentary`, `TIL.body`, `Project.body/summary`), edited only through the Django admin. To run prose skills on it and write changes back safely, use the `dump_content` / `load_content` management commands — never raw SQL, never the admin browser forms.

Why: raw SQL mangles markdown quoting and **bypasses `Model.save()`** (status/is_draft sync + the `blog.signals` auto-tag signal). These commands go through the ORM, so all of that fires correctly.

## Workflow

Always work **local-first**. Promoting to production is a separate, deliberate, approved step.

1. **Sync prod content into local** (so you're editing real content):
   ```
   make sync-db-from-prod
   ```
   Skip if you only need local content or already synced this session.

2. **Export the target content to files:**
   ```
   docker exec minimalwave-blog-container python manage.py dump_content --type entry --slug <slug>
   ```
   Writes `content/<type>-<slug>-<field>.md` (one file per markdown field), each with YAML front-matter (`type/pk/slug/field/title`). `--type` is one of `entry|blogmark|til|project`; use `--all` to dump everything. `content/` is gitignored.

3. **Run the requested prose skill(s) on the file body** — de-slopper, zinsser, analyze-prose, diagnose-then-humanize, etc. Edit only the markdown **below** the `---` front-matter block; leave the front-matter untouched (it routes the write). A markdown formatter hook may add a blank line after the front-matter — harmless, the loader strips leading/trailing blank lines.

4. **Show the accept gate** — the diff of DB-current vs the edited file:
   ```
   docker exec minimalwave-blog-container python manage.py load_content content/<file>.md --dry-run
   ```
   This prints a unified diff (baseline = the live DB row) and writes nothing. Present it to the user for approval. (If you prefer git, you can also commit the initial dump and use `git diff` — but `--dry-run` is self-contained and always diffs against the true source of truth.)

5. **On the user's acceptance, write it back** (local DB):
   ```
   docker exec minimalwave-blog-container python manage.py load_content content/<file>.md
   ```
   Only files the user accepted. The command re-shows the diff, then saves via the ORM.

6. **Verify rendering** at `http://localhost:8000/...` — markdown, image shortcodes, and formatting intact.

7. **Promote to production** (only when the user asks). Run the same `load_content` against the production database. This is a **live production write** and will hit Claude Code's approval gate — that's expected and correct; get explicit user approval first. See "Promoting to prod" below.

## Commands

- `dump_content --type <t> [--slug <s>] [--all] [--output-dir content]` — DB → files.
- `load_content <files...> [--dry-run]` — files → DB via ORM. `--dry-run` is the accept gate (diff only, no write).

Safety built in: `load_content` verifies the file's `slug` still matches the pk's current slug (guards against stale files / wrong DB) and reports `unchanged` when a file matches the DB (idempotent round-trips).

## Promoting to prod

`load_content` uses whatever database the Django settings point at. To write accepted edits to production, run it with the production `DATABASE_URL` in the environment (the `.env` `DATABASE_URL` is the Azure Postgres connection; append `?sslmode=require`). Prefer running it **inside the app container on Azure** (`az webapp ssh` → `cd /home/site/wwwroot && python manage.py load_content ...`) so it uses the same env and hashers as the running app. Treat every prod write as deliberate and get user sign-off; the harness will also require approval.

## Do not

- Do not edit content via raw `psql UPDATE` (mangles markdown, skips `save()`/signals).
- Do not drive the admin edit forms in a browser (fragile, no clean diff, live if prod).
- Do not edit the YAML front-matter of a dumped file (it routes the write).
- Do not commit `content/` (it's gitignored; dumps can contain unpublished drafts).
