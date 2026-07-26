"""
Studio Discord Bot — A dark bridge between Discord and the AI Studio.

Slash Commands:
  /projects          — List all projects in the forge
  /project <name>    — Show project Bible summary
  /write <project>   — Write the next chapter via the Director
  /art <project> <prompt> — Generate an image via ComfyUI
  /director <project> <message> — Speak to the Director agent
  /export <project> <format> — Export and receive the project file
  /presets <project> — List saved art style presets
"""

import asyncio
import io
import json
import os
import sys
from pathlib import Path

import discord
from discord import app_commands
import httpx

# ── Config ──────────────────────────────────

STUDIO_API = os.environ.get("STUDIO_API_URL", "http://127.0.0.1:8800/api")
API_TIMEOUT = 120  # seconds for long operations (write, generate)

# ── Discord client ──────────────────────────

# Pure slash-command bot — no message content, no privileged intents
intents = discord.Intents(guilds=True, voice_states=False, messages=False)

class StudioBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"  Slash commands synced: {len(self.tree.get_commands())}")

client = StudioBot()


# ── API helpers ─────────────────────────────

async def api_get(path: str) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{STUDIO_API}{path}", timeout=30)
        r.raise_for_status()
        return r.json()

async def api_post(path: str, data: dict = None, timeout: int = API_TIMEOUT) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"{STUDIO_API}{path}",
            json=data or {},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json()


# ── Slash Commands ──────────────────────────


@client.tree.command(name="projects", description="List all projects in the forge")
async def cmd_projects(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    try:
        data = await api_get("/projects")
        projs = data.get("projects", [])
        if not projs:
            embed = discord.Embed(
                title="The Forge is Empty",
                description="No projects yet. Forge one at the Studio.",
                color=discord.Color.dark_purple(),
            )
            await interaction.followup.send(embed=embed)
            return

        embed = discord.Embed(
            title="\u2694\uFE0F AI Studio — Projects",
            color=discord.Color.dark_red(),
        )
        for p in projs:
            chapters = p.get("chapter_count", "?")
            characters = p.get("character_count", "?")
            embed.add_field(
                name=f"**{p.get('title', p['name'])}** ({p.get('genre', 'no genre')})",
                value=f"Chapters: {chapters} | Characters: {characters}\n`{p['name']}`",
                inline=False,
            )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)


@client.tree.command(name="project", description="Show a project's Bible summary")
@app_commands.describe(name="The project name (not the title)")
async def cmd_project(interaction: discord.Interaction, name: str):
    await interaction.response.defer(ephemeral=False)
    try:
        data = await api_get(f"/projects/{name}")
        bible = data.get("bible", {})
        embed = discord.Embed(
            title=bible.get("title", name),
            color=discord.Color.dark_purple(),
        )
        embed.add_field(name="Genre", value=bible.get("genre", "—"), inline=True)
        embed.add_field(name="Tone", value=bible.get("tone", "—"), inline=True)

        overview = bible.get("overview", "")
        if overview:
            embed.add_field(
                name="Overview",
                value=overview[:500] + ("..." if len(overview) > 500 else ""),
                inline=False,
            )

        embed.add_field(name="Chapters", value=str(len(bible.get("chapters", []))), inline=True)
        embed.add_field(name="Characters", value=str(len(bible.get("characters", []))), inline=True)
        embed.add_field(name="Locations", value=str(len(bible.get("locations", []))), inline=True)
        embed.add_field(name="Outline Points", value=str(len(bible.get("story_outline", []))), inline=True)
        embed.add_field(name="World Rules", value=str(len(bible.get("world_rules", []))), inline=True)
        embed.add_field(name="Timeline Events", value=str(len(bible.get("timeline", []))), inline=True)
        embed.add_field(name="Generated Images", value=str(len(bible.get("generated_images", []))), inline=True)
        embed.add_field(name="Art Presets", value=str(len(bible.get("art_presets", []))), inline=True)

        updated = bible.get("updated", "")
        if updated:
            embed.set_footer(text=f"Last updated: {updated[:19].replace('T', ' ')} UTC")

        await interaction.followup.send(embed=embed)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await interaction.followup.send(
                f"Project `{name}` not found. Use `/projects` to see all projects.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)


@client.tree.command(name="write", description="Write the next chapter via the Director agent")
@app_commands.describe(project="The project name")
async def cmd_write(interaction: discord.Interaction, project: str):
    await interaction.response.defer(ephemeral=False)
    try:
        data = await api_post(f"/projects/{project}/chapters/generate", timeout=API_TIMEOUT)
        chapter = data.get("chapter", {})
        chapter_num = data.get("chapter_number", "?")

        embed = discord.Embed(
            title=f"\u270D\uFE0F Chapter {chapter_num}: {chapter.get('title', 'Untitled')}",
            description=f"Written for **{project}**",
            color=discord.Color.dark_red(),
        )
        content = chapter.get("content", "")
        if content:
            embed.add_field(
                name="Preview",
                value=content[:1000] + ("..." if len(content) > 1000 else ""),
                inline=False,
            )
        embed.set_footer(text=f"Chapter ID: {chapter.get('id', '?')} | Generated by Director Agent")
        await interaction.followup.send(embed=embed)
    except httpx.HTTPStatusError as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)


@client.tree.command(name="art", description="Generate an image via ComfyUI")
@app_commands.describe(
    project="The project name",
    prompt="Describe the image you want to create",
    model="ComfyUI checkpoint model (default: dreamShaper)",
)
async def cmd_art(
    interaction: discord.Interaction,
    project: str,
    prompt: str,
    model: str = "dreamShaper.safetensors",
):
    await interaction.response.defer(ephemeral=False)
    try:
        data = await api_post(
            f"/projects/{project}/generate",
            {
                "prompt": prompt,
                "model": model,
                "width": 1024,
                "height": 1024,
                "steps": 25,
                "cfg": 7.0,
            },
            timeout=API_TIMEOUT,
        )
        result = data.get("result", {})
        if result.get("error"):
            await interaction.followup.send(f"Generation failed: {result['error']}", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"\U0001F5BC\uFE0F Art Generated",
            description=f"For **{project}**\nPrompt: *{prompt[:500]}*",
            color=discord.Color.dark_purple(),
        )
        if result.get("seed"):
            embed.add_field(name="Seed", value=str(result["seed"]), inline=True)
        if result.get("model"):
            embed.add_field(name="Model", value=result["model"].replace(".safetensors", ""), inline=True)
        if result.get("size_bytes"):
            embed.add_field(name="Size", value=f"{result['size_bytes'] // 1024} KB", inline=True)

        # Send the image
        filename = result.get("filename", "")
        if filename:
            img_url = f"{STUDIO_API}/projects/{project}/images/{filename}"
            embed.set_image(url=img_url)

        await interaction.followup.send(embed=embed)
    except httpx.HTTPStatusError as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)


@client.tree.command(name="director", description="Speak to the Director agent")
@app_commands.describe(
    project="The project name (or 'none' for general chat)",
    message="What you want to say to the Director",
)
async def cmd_director(interaction: discord.Interaction, project: str, message: str):
    await interaction.response.defer(ephemeral=False)
    try:
        data = await api_post(
            "/chat",
            data={
                "message": message,
                "project_name": project,
                "messages": [],
            },
            timeout=API_TIMEOUT,
        )
        response = data.get("response", "Silence...")
        embed = discord.Embed(
            title="Director Speaks",
            description=response[:1900],
            color=discord.Color.dark_green(),
        )
        embed.set_footer(text=f"Project: {project}")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)


@client.tree.command(name="export", description="Export a project and receive the file")
@app_commands.describe(
    project="The project name",
    format="Export format: markdown, pdf, or epub",
)
@app_commands.choices(format=[
    app_commands.Choice(name="Markdown", value="markdown"),
    app_commands.Choice(name="PDF", value="pdf"),
    app_commands.Choice(name="EPUB", value="epub"),
])
async def cmd_export(interaction: discord.Interaction, project: str, format: str):
    await interaction.response.defer(ephemeral=False)
    try:
        export_url = f"{STUDIO_API}/projects/{project}/export/{format}"
        async with httpx.AsyncClient() as c:
            r = await c.get(export_url, timeout=60)
            r.raise_for_status()

            content_type = r.headers.get("content-type", "application/octet-stream")
            ext_map = {"markdown": "md", "pdf": "pdf", "epub": "epub"}
            ext = ext_map.get(format, format)

            # For PDF and EPUB, send as file attachment
            if format in ("pdf", "epub"):
                await interaction.followup.send(
                    file=discord.File(
                        io.BytesIO(r.content),
                        filename=f"{project}.{ext}",
                    )
                )
            else:
                await interaction.followup.send(
                    f"```markdown\n{r.text[:1900]}\n```"
                )
    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)


@client.tree.command(name="presets", description="List saved art style presets for a project")
@app_commands.describe(project="The project name")
async def cmd_presets(interaction: discord.Interaction, project: str):
    await interaction.response.defer(ephemeral=False)
    try:
        data = await api_get(f"/projects/{project}")
        presets = data.get("bible", {}).get("art_presets", [])
        if not presets:
            await interaction.followup.send(f"No art presets saved for `{project}`.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"\U0001F3A8 Art Presets — {project}",
            color=discord.Color.dark_gold(),
        )
        for p in presets:
            suffix = p.get("prompt_suffix", "")
            meta = []
            if p.get("model"):
                meta.append(p["model"].replace(".safetensors", ""))
            meta.append(f"{p.get('width', '?')}\u00d7{p.get('height', '?')}")
            meta.append(f"{p.get('steps', '?')} steps")
            meta.append(f"CFG {p.get('cfg', '?')}")
            value = " \u00b7 ".join(meta)
            if suffix:
                value += f"\n> \"{suffix[:100]}\""
            embed.add_field(
                name=p.get("name", "Unnamed"),
                value=value,
                inline=False,
            )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)


# ── Entry point ─────────────────────────────

def main():
    from dotenv import load_dotenv
    load_dotenv()
    token = os.environ.get("DISCORD_BOT_TOKEN") or os.environ.get("DISCORD_STUDIO_BOT_TOKEN")
    if not token:
        print("ERROR: DISCORD_BOT_TOKEN not set. Set it in .env or environment.")
        sys.exit(1)
    print("  Studio Discord Bot rising...")
    client.run(token)


if __name__ == "__main__":
    main()
