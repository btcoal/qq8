# qq8 Design System & Site Architecture Reference

All pages on **qq8** share a crisp, white-ground newspaper layout inspired by *Bloomberg* and *The Wall Street Journal*, paired with consistent Light/Dark and Default/Wide reader toggles persisted via `localStorage`.

## 1. Repository Layout

```text
/
├── index.html                   # Publication front page (/)
├── 404.html                     # Custom not-found page
├── CNAME                        # Contains: www.qqeight.com
├── .nojekyll                    # Disables Jekyll processing on GitHub Pages
└── <slug>/
    ├── index.html               # Article page (/<slug>/)
    └── images/                  # Locally hosted, magic-byte-verified public images
```

Keep source PDFs, scratch drafts, and private workspace notes out of the public git tree (exclude them in `.gitignore` if kept in the same folder locally).

## 2. CSS Tokens (Light & Dark Modes)

Include these exact CSS custom properties and anti-FOUC `<script>` hooks:

```css
:root {
  --bg-paper: #ffffff;
  --bg-card: #f7f8fa;
  --bg-surface: #ffffff;
  --bg-code: #f1f3f5;
  --bg-table-alt: #f8f9fb;
  --ink-primary: #000000;
  --ink-body: #1f2328;
  --ink-muted: #596068;
  --ink-sub: #40454c;
  --ink-code: #111827;
  --accent-blue: #0274b6;
  --accent-blue-dark: #004e7c;
  --border-rule: #d0d5dd;
  --border-light: #e5e7eb;
  --border-code: #e2e6eb;
  --progress-track: #eceef2;
  --btn-bg: #f7f8fa;
  --btn-active-bg: #000000;
  --btn-active-ink: #ffffff;
  --font-serif: "Georgia", "Times New Roman", "Iowan Old Style", serif;
  --font-sans: "Helvetica Neue", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
  --font-mono: ui-monospace, "SFMono-Regular", Menlo, Monaco, Consolas, monospace;
  --layout-width: 820px;
}

html[data-width="wide"] {
  --layout-width: 1240px;
}

html[data-theme="dark"] {
  --bg-paper: #0d1014;
  --bg-card: #161b22;
  --bg-surface: #12161c;
  --bg-code: #1d242e;
  --bg-table-alt: #141920;
  --ink-primary: #f3f5f8;
  --ink-body: #d5dce4;
  --ink-muted: #939eab;
  --ink-sub: #b4bec9;
  --ink-code: #e6edf3;
  --accent-blue: #4aa8ff;
  --accent-blue-dark: #7ec2ff;
  --border-rule: #2d3643;
  --border-light: #222933;
  --border-code: #2c3542;
  --progress-track: #1c2128;
  --btn-bg: #161b22;
  --btn-active-bg: #f3f5f8;
  --btn-active-ink: #0d1014;
}
```

### Shared Pre-Paint Script & `localStorage` Keys

Place this inline script in `<head>` right before `<style>` so saved preferences apply without flash of unstyled content:

```html
<script>
  (function () {
    try {
      if (localStorage.getItem("qq8-theme") === "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
      }
      if (localStorage.getItem("qq8-width") === "wide") {
        document.documentElement.setAttribute("data-width", "wide");
      }
    } catch (e) {}
  })();
</script>
```

## 3. Metadata & Favicon Template

Every article `<head>` should include canonical, Open Graph, Twitter Card tags, and the inline SVG `qq8` favicon:

```html
<meta name="description" content="...">
<link rel="canonical" href="https://www.qqeight.com/<slug>/">
<meta property="og:site_name" content="qq8">
<meta property="og:type" content="article">
<meta property="og:title" content="...">
<meta property="og:description" content="...">
<meta property="og:url" content="https://www.qqeight.com/<slug>/">
<meta property="og:image" content="https://www.qqeight.com/<slug>/images/<hero-image>.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' fill='%23000'/%3E%3Ctext x='50%25' y='54%25' dominant-baseline='middle' text-anchor='middle' fill='%23fff' font-family='Helvetica Neue,Arial,sans-serif' font-weight='900' font-size='28' letter-spacing='-1'%3Eqq8%3C/text%3E%3C/svg%3E">
```

## 4. Structural Markup Patterns

* **Top progress bar:** `<div class="progress-track" aria-hidden="true"><div class="progress-fill" id="progressFill"></div></div>`
* **Masthead (`.masthead` > `.masthead-inner`):**
  * Left (`.brand-mark`): `<a class="brand-name" href="../">qq8</a>` (use `./` on front page, `/` on `404.html`) + `<span class="brand-section">Topic Label</span>`.
  * Right (`.masthead-right`): `.nav-links` (always ending with `<a href="#sources">Sources</a>`, never `Documents`) + `.controls-group` containing `#widthDefaultBtn`, `#widthWideBtn`, and `#darkModeBtn`.
* **Header (`.article-header`):** `.kicker-row` (square blue mark via `::before`), `<h1>`, `.standfirst`, `.meta-bar` (`By <strong>qq8 Staff</strong>`, `Published`, `Reading time`).
* **Body column (`.content-col`):** `max-width: var(--layout-width)` unified across prose `<p>`, `.figure-block` (single `<figure>` or two-up `.figure-grid`), `blockquote.pullquote`, `.table-card` (`tabular-nums`), and `.callout-box`.
* **Inline typography:** Do not wrap technical terms, chip/model names (such as `H100` or `B200`), or regulatory codes in inline `<code>` tags; keep monospace formatting strictly for genuine `<pre><code>` code blocks.
* **Sources (`.sources-section#sources`):** Heading `<h2>Primary Sources &amp; Technical References</h2>`, responsive `.sources-grid` of `.source-card` items linking directly to canonical external URLs.
* **Footer (`.site-footer`):**
  ```html
  <footer class="site-footer">
    <span>© 2026 <a href="../">qq8</a> (qqeight.com) · By qq8 Staff</span>
    <span>Section Name</span>
  </footer>
  ```
  Never leave `"Published locally for preview"` in committed HTML.
