---
name: qq8-editorial
description: >-
  Editorial, structural, visual, and publishing workflow for drafting, revising,
  formatting, and publishing analytical articles for the qq8 publication (www.qqeight.com).
  Use this skill when writing or editing qq8 articles, sourcing public imagery, updating
  the front page, or validating article HTML before publishing.
---

# qq8 Editorial & Publishing Skill

Follow this standard when drafting, editing, or publishing long-form analytical journalism for **qq8** (`https://www.qqeight.com`).

## 1. Publication Identity & Tone

* **Publication & byline:** Publish under **qq8** (`https://www.qqeight.com`), with the default byline `By qq8 Staff`.
* **Editorial posture:** Write with the brisk, authoritative register of *Bloomberg* or *The Wall Street Journal*—analytical, concrete, and unadorned. Avoid tinted essay-magazine aesthetics or melodramatic flourishes.
* **Header hygiene:** Omit `"SPECIAL REPORT"` labels, `"Dateline: ..."` lines, and top-of-page source button pills. Lead cleanly with the kicker, headline, standfirst, byline metadata, and opening figure.

## 2. Prose, Structure & Rhythm

* **No bulleted or numbered lists in prose:** Never use `<ul>`, `<ol>`, or `<li>` in article bodies. Rewrite sequences and multi-part rules as flowing paragraphs, reserving structured HTML `.table-card` tables for genuine tabular comparisons and `.callout-box` blocks for compact caveats or drafting ambiguities.
* **Short paragraphs:** Target roughly 50–90 words per paragraph, especially in legal, technical, or regulatory explanations. Split dense walls of text (>120 words) into single-idea beats.
* **Varied sentence rhythm:** Alternate crisp short sentences with longer explanatory sentences. Avoid chaining multiple consecutive clause-heavy sentences.
* **Lead with human and institutional stakes:** Ground technical and regulatory pieces early in real-world actors, investment consequences, operational deadlines, and political conflict before diving into mechanics.
* **Fewer parenthetical definitions:** Explain an unfamiliar term or acronym once smoothly in prose, then trust the reader.
* **Familiar place names and acronyms:** Use common country names (`China`, `United States`, `United Arab Emirates` or `UAE`). Avoid formal acronyms like `PRC` or `People's Republic of China`, and do not spell out obvious country abbreviations.
* **Oxford comma:** Use the serial (Oxford) comma consistently in every series of three or more items (`A, B, and C`).
* **Sparse, semantic boldface:** Never scatter emboldened keywords across body paragraphs for skimming. Reserve `<strong>` in running body text for at most a handful of genuine semantic emphases.
* **No inline code formatting on technical terms:** Never wrap chip or model names (`H100`, `B200`, `GB200`, `DeepSeek-V4`, `Kimi K3`), regulatory codes (`ECCN 3A090.a`, `RIN 0694-AK50`), metrics, libraries, handles, or URLs in markdown backticks or inline `<code>` tags; reserve `<code>` strictly for genuine code snippets inside `<pre><code>`.
* **Plain-English legal citations:** Do not clutter prose with statutory or code section citations (`§ 744.24(a)(1)`, `15 CFR`, `50 U.S.C.`, `Supplement No. 1`, `Note 2`). Explain legal triggers, rules, and exceptions clearly while keeping substantive identifiers readers or practitioners actually look up (such as `RIN` numbers and `ECCN` codes).

## 3. Epistemic Rigor, Attribution & Causality

* **Never use colloquial "prove":** Reserve `prove`, `proved`, `proven`, and `proof` strictly for formal logical or mathematical proofs. Describe empirical, forensic, or journalistic findings with precise verbs: `showed`, `indicated`, `reproduced`, `corroborated`, `matched`, or `found statistical signatures`.
* **No vague attribution:** Replace generic attributions (`officials said`, `policymakers argued`, `reporters revealed`, `an engineer posted`) with named people, titles, news outlets, journalists, repositories, usernames, pull requests, and dates wherever known.
* **Strict causal discipline:** Never imply—directly or through juxtaposition—that an independent public study caused a regulation merely because it appeared shortly beforehand. Distinguish the underlying policy drivers (intelligence, industry reporting, multi-month agency deliberations) from independent research used to illustrate scale.
* **No unverified superlatives or forced rhetoric:** Avoid overclaims (`the first public`, `the missing forensic link`) unless verified, and avoid canned closings (`The irony is hard to miss...`). End articles cleanly on the strategic pivot, open tensions, and real-world tests ahead.
* **Credit caveats explicitly:** When incorporating legal alerts or technical papers, attribute ambiguities, methodological limits, and counter-interpretations directly to their authors.

## 4. Visuals, Layout & Sources

* Consult [references/design-system.md](./references/design-system.md) for the exact CSS variables, typography, light/dark themes, reading progress bar, toggles, and structural markup.
* **Unified column width:** Body prose, figures, pull quotes, callouts, and tables must share the same column width (`820px` default, `1240px` wide).
* **Public imagery:** Download official public images locally into `<slug>/images/`, link them via relative `images/<file>` paths, credit the origin directly in `<figcaption>`, and verify downloaded files are valid binary images (never HTML anti-bot/WAF challenge pages saved with an image extension).
* **Sources section:** Name the navigation link `Sources` (never `Documents`) and the bottom reference block `Primary Sources & Technical References` (`#sources`). Link cards directly to original public URLs; never commit third-party source PDFs into the public site repository.

## 5. Publishing & Verification Workflow

1. **Author the article directory:** Create `/<slug>/index.html` and `/<slug>/images/` with relative links (`../` for the front page, `images/...` for figures), complete canonical/Open Graph/Twitter metadata pointing to `https://www.qqeight.com/<slug>/`, and production footer copy (never `"Published locally for preview"`).
2. **Feature on the front page:** Update root `index.html` with the headline, standfirst, relative hero image (`<slug>/images/...`), and link (`<slug>/`).
3. **Run automated checks:**
   ```bash
   python3 .agents/skills/qq8-editorial/scripts/verify_article.py
   ```
   Use `--strict` before final publication to catch warnings (heavy bolding, >120-word paragraphs, vague attribution, or causal/overclaim phrasing) as errors.
4. **Local preview & visual check:** Serve the repo root locally (`python3 -m http.server --bind 127.0.0.1`) and verify Default vs. Wide widths and Light vs. Dark mode before pushing.
5. **Publish cleanly:** Confirm `git status` contains only intended public site assets (never local notes, source PDFs, or working drafts), commit to `main`, and push to GitHub Pages.
