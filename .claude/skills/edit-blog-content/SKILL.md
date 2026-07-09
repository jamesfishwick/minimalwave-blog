---
name: edit-blog-content
description: >-
  Improve the writing in existing posts on James's Postgres-backed Django blog and save the result. Reach for this whenever a user points at content they've already published — an Entry, Blogmark, TIL, or Project, or one of its fields (body, summary, commentary, intro) — and asks to tighten, rewrite, clean up, de-slop, zinsser, or fix "AI-sounding" prose, then wants it persisted back (to the database, postgres, or the db, optionally after syncing prod down or showing a diff first). Any request that combines "make this post read better" with "and save/update/load it" belongs here, whether phrased about the latest post, a named slug, or several recent ones. The skill exports each row to a file, runs the prose skill, shows a diff you approve, and writes back through the Django ORM. Not for drafting new posts, changing dates or other metadata, repairing markdown syntax, or de-slopping repo files like READMEs.
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

7. **Promote to production** (only when the user asks). Use `make load-content-prod` (see "Promoting to prod" below). This is a **live production write** and will hit Claude Code's approval gate — that's expected and correct; get explicit user approval first.

## Commands

- `dump_content --type <t> [--slug <s>] [--all] [--output-dir content]` — DB → files.
- `load_content <files...> [--dry-run]` — files → DB via ORM. `--dry-run` is the accept gate (diff only, no write).
- `scripts/load-content-to-production.sh` (a.k.a. `make load-content-prod`) — the prod-promotion wrapper. See "Promoting to prod".

Safety built in: `load_content` verifies the file's `slug` still matches the pk's current slug (guards against stale files / wrong DB) and reports `unchanged` when a file matches the DB (idempotent round-trips).

## Promoting to prod

Use the wrapper, not a hand-rolled command: **`scripts/load-content-to-production.sh`**, exposed as two Make targets. It reads `DATABASE_URL` + `SECRET_KEY` from `.env`, appends `sslmode=require`, snapshots current prod content to `data/content-backups/prod-content-<ts>/` (a restore point), runs a mandatory dry-run, prompts for confirmation, then writes via the ORM with production settings. Secrets are passed to the container by env-var **name** only, so they never appear in a printed command.

```
# Preview only (no writes, no snapshot):
make load-content-prod-dry FILES="content/entry-40-reranking-summary.md"
make load-content-prod-dry ALL=1

# Promote (snapshot -> dry-run -> confirm -> write):
make load-content-prod FILES="content/entry-40-reranking-summary.md"
make load-content-prod ALL=1
```

Get explicit user sign-off first; the harness will also require approval on the write. **Roll back** by pointing the script at a snapshot: `./scripts/load-content-to-production.sh data/content-backups/prod-content-<ts>/<file>.md`.

The script targets the local `minimalwave-blog-container` (override with `CONTENT_CONTAINER=<name>`); it uses the same code + files you edited, just pointed at the prod DB. Running `load_content` by hand inside the Azure app container (`az webapp ssh` → `cd /home/site/wwwroot`) also works but requires getting the edited files onto that container first, so the wrapper is the default path.

### Batch de-slopping many posts

For a whole-blog pass (run de-slopper / house-style / etc. across every post): `dump_content --all`, then edit the files (fan out to parallel subagents by size-balanced batches for speed), diff each against a pre-edit copy to catch any over-editing, `load_content` the changed files to local, verify, then `make load-content-prod ALL=1`. Keep automated passes **sentence-level** (don't delete paragraphs) and never bake `[AUTHOR NEEDED]` tags into files that auto-publish.

## Do not

- Do not edit content via raw `psql UPDATE` (mangles markdown, skips `save()`/signals).
- Do not drive the admin edit forms in a browser (fragile, no clean diff, live if prod).
- Do not edit the YAML front-matter of a dumped file (it routes the write).
- Do not commit `content/` (it's gitignored; dumps can contain unpublished drafts).
