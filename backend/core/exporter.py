"""
Export Pipeline — compiles a Project Bible into Markdown, PDF, and EPUB.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

DATA_DIR = os.environ.get("STUDIO_DATA_DIR", "./projects")


def _load_bible(project_name: str) -> dict:
    path = Path(DATA_DIR) / project_name / "bible.json"
    if not path.exists():
        raise FileNotFoundError(f"Project '{project_name}' not found")
    with open(path) as f:
        return json.load(f)


def _image_path(project_name: str, filename: str) -> Optional[Path]:
    """Resolve an image filename to its disk path."""
    candidates = [
        Path(DATA_DIR) / project_name / "images" / filename,
        Path(DATA_DIR) / "_generated" / filename,
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


# ── Markdown Export ────────────────────────────────────────────────


def export_markdown(project_name: str) -> str:
    """Export the project as a complete Markdown document."""
    bible = _load_bible(project_name)

    lines = []
    lines.append(f"# {bible.get('title', project_name)}")
    lines.append("")
    if bible.get("genre"):
        lines.append(f"**Genre:** {bible['genre']}")
    if bible.get("tone"):
        lines.append(f"**Tone:** {bible['tone']}")
    lines.append("")

    # Overview
    if bible.get("overview"):
        lines.append("## Overview")
        lines.append("")
        lines.append(bible["overview"])
        lines.append("")

    # Characters
    if bible.get("characters"):
        lines.append("## Characters")
        for c in bible["characters"]:
            desc = c.get("description", "")
            role = c.get("role", "")
            tag = f" — *{role}*" if role else ""
            lines.append(f"- **{c['name']}**{tag}: {desc}")
        lines.append("")

    # Locations
    if bible.get("locations"):
        lines.append("## Locations")
        for loc in bible["locations"]:
            desc = loc.get("description", "")
            suffix = f" — {desc}" if desc else ""
            lines.append(f"- **{loc['name']}**{suffix}")
        lines.append("")

    # Story Outline
    if bible.get("story_outline"):
        lines.append("## Story Outline")
        for i, pt in enumerate(bible["story_outline"], 1):
            lines.append(f"{i}. {pt}")
        lines.append("")

    # World Rules
    if bible.get("world_rules"):
        lines.append("## World Rules")
        for r in bible["world_rules"]:
            lines.append(f"- {r}")
        lines.append("")

    # Timeline
    if bible.get("timeline"):
        lines.append("## Timeline")
        for entry in bible["timeline"]:
            lines.append(f"- {entry}")
        lines.append("")

    # Chapters — the actual story
    if bible.get("chapters"):
        lines.append("---")
        lines.append("")
        for i, ch in enumerate(bible["chapters"], 1):
            ch_title = ch.get("title", f"Chapter {i}")
            lines.append(f"# {ch_title}")
            lines.append("")
            if ch.get("content"):
                lines.append(ch["content"])
                lines.append("")
            lines.append("---")
            lines.append("")

    # Generated images metadata
    if bible.get("generated_images"):
        lines.append("## Generated Images")
        lines.append("")
        for img in bible["generated_images"]:
            prompt = img.get("prompt", "Untitled")
            model = img.get("model", "unknown")
            seed = img.get("seed", "?")
            lines.append(f"- **Prompt:** {prompt}")
            lines.append(f"  - Model: {model}, Seed: {seed}")
            lines.append("")

    return "\n".join(lines)


# ── PDF Export ─────────────────────────────────────────────────────


def export_pdf(project_name: str, output_path: Optional[str] = None) -> str:
    """Export the project as a PDF document with embedded images."""
    from fpdf import FPDF

    bible = _load_bible(project_name)
    title = bible.get("title", project_name)

    if output_path is None:
        project_dir = Path(DATA_DIR) / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(project_dir / "export.pdf")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Register Unicode-compatible font (DejaVuSans is available on Ubuntu)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path)
        pdf.add_font("DejaVu", "B", font_bold_path)
        # No DejaVuSans-Oblique exists; use DejaVuSerif for italic styling
        pdf.add_font("DejaVu", "I", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",)
        FONT = "DejaVu"
    else:
        FONT = "Helvetica"  # fallback, but will fail on Unicode

    # ── Title Page ──
    pdf.add_page()
    pdf.set_font(FONT, "B", 28)
    pdf.ln(60)
    pdf.cell(0, 20, title, new_x="LMARGIN", new_y="NEXT", align="C")
    if bible.get("genre"):
        pdf.set_font(FONT, "", 14)
        pdf.cell(0, 10, bible["genre"], new_x="LMARGIN", new_y="NEXT", align="C")
    if bible.get("tone"):
        pdf.set_font(FONT, "I", 12)
        pdf.cell(0, 10, bible["tone"], new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(20)
    pdf.set_font(FONT, "", 10)
    pdf.cell(0, 8, f"Generated by AI Studio — {datetime.now().strftime('%B %d, %Y')}",
             new_x="LMARGIN", new_y="NEXT", align="C")

    # ── Table of Contents placeholder ──
    pdf.add_page()
    pdf.set_font(FONT, "B", 18)
    pdf.cell(0, 15, "Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    toc_entries = []
    if bible.get("overview"):
        toc_entries.append("Overview")
    if bible.get("characters"):
        toc_entries.append("Characters")
    if bible.get("locations"):
        toc_entries.append("Locations")
    if bible.get("story_outline"):
        toc_entries.append("Story Outline")
    for i, ch in enumerate(bible.get("chapters", []), 1):
        toc_entries.append(ch.get("title", f"Chapter {i}"))

    pdf.set_font(FONT, "", 12)
    for entry in toc_entries:
        pdf.cell(0, 8, f"  {entry}", new_x="LMARGIN", new_y="NEXT")

    # ── Helper: write a text block ──
    def write_text_block(text: str, size: int = 11):
        pdf.set_font(FONT, "", size)
        # Replace special chars, handle paragraphs
        paragraphs = str(text).split("\n")
        for para in paragraphs:
            if para.strip():
                pdf.multi_cell(0, 5.5, para.strip())
            pdf.ln(1)

    # ── Overview ──
    if bible.get("overview"):
        pdf.add_page()
        pdf.set_font(FONT, "B", 16)
        pdf.cell(0, 12, "Overview", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        write_text_block(bible["overview"])

    # ── Characters ──
    if bible.get("characters"):
        pdf.add_page()
        pdf.set_font(FONT, "B", 16)
        pdf.cell(0, 12, "Characters", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        for c in bible["characters"]:
            pdf.set_font(FONT, "B", 12)
            name = c.get("name", "?")
            role = c.get("role", "")
            label = f"{name} ({role})" if role else name
            pdf.cell(0, 8, label, new_x="LMARGIN", new_y="NEXT")
            if c.get("description"):
                pdf.set_font(FONT, "", 10)
                pdf.multi_cell(0, 5, c["description"])
            pdf.ln(3)

    # ── Locations ──
    if bible.get("locations"):
        pdf.add_page()
        pdf.set_font(FONT, "B", 16)
        pdf.cell(0, 12, "Locations", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        for loc in bible["locations"]:
            pdf.set_font(FONT, "B", 12)
            pdf.cell(0, 8, loc.get("name", "?"), new_x="LMARGIN", new_y="NEXT")
            if loc.get("description"):
                pdf.set_font(FONT, "", 10)
                pdf.multi_cell(0, 5, loc["description"])
            pdf.ln(3)

    # ── Chapters ──
    if bible.get("chapters"):
        for i, ch in enumerate(bible["chapters"], 1):
            pdf.add_page()
            ch_title = ch.get("title", f"Chapter {i}")
            pdf.set_font(FONT, "B", 20)
            pdf.cell(0, 15, ch_title, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

            # Insert inline images for this chapter if any exist (matched by chapter title)
            content = ch.get("content", "")
            if content:
                write_text_block(content, 11)

            # Insert per-chapter images
            chapter_imgs = [
                img for img in bible.get("generated_images", [])
                if img.get("chapter") == ch_title or img.get("chapter_id") == ch.get("id")
            ]
            for img in chapter_imgs:
                img_path = _image_path(project_name, img.get("filename", ""))
                if img_path:
                    try:
                        pdf.ln(3)
                        pdf.image(str(img_path), x=None, w=140)
                        pdf.set_font(FONT, "I", 8)
                        pdf.cell(0, 5, f"\"{img.get('prompt', '')[:80]}\" — seed {img.get('seed', '?')}",
                                 new_x="LMARGIN", new_y="NEXT", align="C")
                    except Exception:
                        pass

    # ── Image Gallery ──
    if bible.get("generated_images"):
        pdf.add_page()
        pdf.set_font(FONT, "B", 16)
        pdf.cell(0, 12, "Image Gallery", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        for img in bible["generated_images"]:
            img_path = _image_path(project_name, img.get("filename", ""))
            if img_path:
                try:
                    pdf.image(str(img_path), x=None, w=140)
                    prompt = img.get("prompt", "")
                    model = img.get("model", "unknown")
                    seed = img.get("seed", "?")
                    pdf.set_font(FONT, "I", 8)
                    pdf.cell(0, 5, f"\"{prompt[:80]}\" — {model} · seed {seed}",
                             new_x="LMARGIN", new_y="NEXT", align="C")
                    pdf.ln(5)
                except Exception:
                    pass

    pdf.output(output_path)
    return output_path


# ── EPUB Export ────────────────────────────────────────────────────


def export_epub(project_name: str, output_path: Optional[str] = None) -> str:
    """Export the project as an EPUB e-book."""
    import markdown
    from ebooklib import epub

    bible = _load_bible(project_name)
    title = bible.get("title", project_name)

    if output_path is None:
        project_dir = Path(DATA_DIR) / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(project_dir / "export.epub")

    book = epub.EpubBook()
    book.set_identifier(f"studio-{project_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    book.set_title(title)
    book.set_language("en")

    if bible.get("genre") or bible.get("tone"):
        author = f"{bible.get('genre', '')}"
        if bible.get("tone"):
            author += f" — {bible['tone']}"
        book.add_author(author)

    # ── CSS ──
    css = """
    body { font-family: Georgia, serif; line-height: 1.6; margin: 5%; }
    h1 { font-size: 1.8em; margin-top: 1.5em; }
    h2 { font-size: 1.4em; margin-top: 1.2em; }
    h3 { font-size: 1.2em; margin-top: 1em; }
    p { margin-bottom: 0.5em; text-indent: 0; }
    .chapter-title { font-size: 2em; margin-top: 2em; margin-bottom: 0.5em; }
    .meta { color: #666; font-style: italic; font-size: 0.9em; }
    img { max-width: 100%; height: auto; margin: 1em 0; }
    .gallery-img { margin: 1em 0; }
    .section-title { font-size: 1.6em; margin-top: 1.5em; border-bottom: 1px solid #ccc; padding-bottom: 0.3em; }
    """
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=css)

    def md_to_html(text: str) -> str:
        return markdown.markdown(text)

    spine = ["nav"]
    toc = []

    # ── Title page ──
    title_content = f"""
    <html><body>
    <div style="text-align:center;margin-top:30%">
      <h1 style="font-size:2.5em">{title}</h1>
      <p class="meta">{bible.get('genre', '')}{' — ' + bible['tone'] if bible.get('tone') else ''}</p>
      <p class="meta">Generated by AI Studio — {datetime.now().strftime('%B %d, %Y')}</p>
    </div>
    </body></html>
    """
    title_page = epub.EpubHtml(title="Title", file_name="title.xhtml", lang="en")
    title_page.content = title_content
    book.add_item(title_page)
    spine.append(title_page)

    # ── Overview ──
    if bible.get("overview"):
        html = f"<h2 class=\"section-title\">Overview</h2><p>{bible['overview']}</p>"
        page = epub.EpubHtml(title="Overview", file_name="overview.xhtml", lang="en")
        page.content = f"<html><body>{html}</body></html>"
        page.add_item(nav_css)
        book.add_item(page)
        spine.append(page)
        toc.append(epub.Link("overview.xhtml", "Overview", "overview"))

    # ── Characters ──
    if bible.get("characters"):
        items = []
        for c in bible["characters"]:
            name = c.get("name", "?")
            role = c.get("role", "")
            desc = c.get("description", "")
            role_tag = f" <em>({role})</em>" if role else ""
            items.append(f"<li><strong>{name}</strong>{role_tag}: {desc}</li>")
        html = f"<h2 class=\"section-title\">Characters</h2><ul>{''.join(items)}</ul>"
        page = epub.EpubHtml(title="Characters", file_name="characters.xhtml", lang="en")
        page.content = f"<html><body>{html}</body></html>"
        page.add_item(nav_css)
        book.add_item(page)
        spine.append(page)
        toc.append(epub.Link("characters.xhtml", "Characters", "characters"))

    # ── Locations ──
    if bible.get("locations"):
        items = []
        for loc in bible["locations"]:
            name = loc.get("name", "?")
            desc = loc.get("description", "")
            desc_tag = f": {desc}" if desc else ""
            items.append(f"<li><strong>{name}</strong>{desc_tag}</li>")
        html = f"<h2 class=\"section-title\">Locations</h2><ul>{''.join(items)}</ul>"
        page = epub.EpubHtml(title="Locations", file_name="locations.xhtml", lang="en")
        page.content = f"<html><body>{html}</body></html>"
        page.add_item(nav_css)
        book.add_item(page)
        spine.append(page)
        toc.append(epub.Link("locations.xhtml", "Locations", "locations"))

    # ── Chapters ──
    if bible.get("chapters"):
        for i, ch in enumerate(bible["chapters"], 1):
            ch_title = ch.get("title", f"Chapter {i}")
            content = ch.get("content", "")

            # Markdown content to HTML
            body_html = ""
            if content:
                body_html = md_to_html(content)

            # Inline images for this chapter
            chapter_imgs = [
                img for img in bible.get("generated_images", [])
                if img.get("chapter") == ch_title or img.get("chapter_id") == ch.get("id")
            ]
            for img in chapter_imgs:
                img_path = _image_path(project_name, img.get("filename", ""))
                if img_path:
                    # Add image as EPUB media
                    with open(img_path, "rb") as f:
                        img_filename = img.get("filename", f"ch{i}.png")
                    img_item = epub.EpubImage(
                            uid=f"img_{img.get('seed', '0')}_{i}",
                            file_name=f"images/{img_filename}",
                            media_type="image/png",
                            content=f.read()
                        )
                    book.add_item(img_item)
                    prompt = img.get("prompt", "")
                    body_html += f'<div class="gallery-img"><img src="images/{img.get("filename", f"ch{i}.png")}" alt="{prompt}"/>'
                    body_html += f'<p class="meta">"{prompt[:100]}" — seed {img.get("seed", "?")}</p></div>'

            page_html = f"""
            <html><body>
            <h1 class="chapter-title">{ch_title}</h1>
            {body_html}
            </body></html>
            """
            page = epub.EpubHtml(title=ch_title, file_name=f"chapter_{i}.xhtml", lang="en")
            page.content = page_html
            page.add_item(nav_css)
            book.add_item(page)
            spine.append(page)
            toc.append(epub.Link(f"chapter_{i}.xhtml", ch_title, f"ch{i}"))

    # ── Image Gallery ──
    if bible.get("generated_images"):
        gallery_items = []
        for img in bible["generated_images"]:
            img_path = _image_path(project_name, img.get("filename", ""))
            if img_path:
                gal_filename = img.get("filename", "gal.png")
                uid = f"gallery_{img.get('seed', '0')}"
                with open(img_path, "rb") as f:
                    gal_img = epub.EpubImage(
                        uid=uid,
                        file_name=f"gallery/{img.get('filename', f'gal.png')}",
                        media_type="image/png",
                        content=f.read()
                    )
                book.add_item(gal_img)
                prompt = img.get("prompt", "")
                model = img.get("model", "unknown")
                seed = img.get("seed", "?")
                gallery_items.append(
                    f'<div class="gallery-img">'
                    f'<img src="gallery/{img.get("filename", "gal.png")}" alt="{prompt}"/>'
                    f'<p class="meta">"{prompt[:80]}" — {model} · seed {seed}</p>'
                    f'</div>'
                )
        if gallery_items:
            gal_page = epub.EpubHtml(title="Image Gallery", file_name="gallery.xhtml", lang="en")
            gal_page.content = f"""
            <html><body>
            <h2 class="section-title">Image Gallery</h2>
            {''.join(gallery_items)}
            </body></html>
            """
            gal_page.add_item(nav_css)
            book.add_item(gal_page)
            spine.append(gal_page)
            toc.append(epub.Link("gallery.xhtml", "Image Gallery", "gallery"))

    # ── Build ──
    book.add_item(nav_css)
    book.toc = toc
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(output_path, book)
    return output_path


# ── Convenience: export all formats ────────────────────────────────


def export_all(project_name: str) -> dict[str, str]:
    """Export the project in all supported formats."""
    project_dir = Path(DATA_DIR) / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    md_path = str(project_dir / "export.md")
    pdf_path = str(project_dir / "export.pdf")
    epub_path = str(project_dir / "export.epub")

    md = export_markdown(project_name)
    with open(md_path, "w") as f:
        f.write(md)

    pdf = export_pdf(project_name, pdf_path)
    epub = export_epub(project_name, epub_path)

    return {
        "markdown": md_path,
        "pdf": pdf_path,
        "epub": epub_path,
    }
