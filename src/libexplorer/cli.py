from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from . import __version__

app = typer.Typer(
    name="libexplorer",
    help="Discover real-world usage of any Python library on GitHub.",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"libexplorer {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = False,
) -> None:
    pass


@app.command()
def analyze(
    library: Annotated[str, typer.Argument(help="Library name, e.g. tenacity")],
    language: Annotated[str, typer.Option("--language", "-l")] = "python",
    top_k: Annotated[int, typer.Option("--top-k", "-k")] = 5,
    limit: Annotated[int, typer.Option("--limit")] = 50,
    skip_cache: Annotated[bool, typer.Option("--skip-cache")] = False,
) -> None:
    """Run the full pipeline: discover → verify → score → extract → summarize → report."""
    from .discovery import discover
    from .extraction import extract_digests
    from .reporting import render
    from .scoring import score
    from .summarization import summarize
    from .verification import verify

    console.rule(f"[bold cyan]Analyzing: {library}[/bold cyan]")

    candidates = discover(library, language=language, limit=limit, skip_cache=skip_cache)
    console.print(f"  [dim]Candidates: {len(candidates)}[/dim]")

    verified = verify(library, candidates, skip_cache=skip_cache)

    ranked = score(library, verified, skip_cache=skip_cache)

    digests = extract_digests(library, ranked, top_k=top_k, skip_cache=skip_cache)

    synthesis = summarize(library, digests)

    out_path = render(library, digests, synthesis)

    console.rule("[bold green]Done[/bold green]")
    console.print(f"\nReport: [link={out_path}]{out_path}[/link]\n")

    _print_summary_table(library, digests)


@app.command()
def discover(
    library: Annotated[str, typer.Argument()],
    language: Annotated[str, typer.Option("--language", "-l")] = "python",
    limit: Annotated[int, typer.Option("--limit")] = 50,
    skip_cache: Annotated[bool, typer.Option("--skip-cache")] = False,
) -> None:
    """Discover candidate repos using GitHub search."""
    from .discovery import discover as _discover

    candidates = _discover(library, language=language, limit=limit, skip_cache=skip_cache)
    console.print(f"Discovered [bold]{len(candidates)}[/bold] candidate repos for [cyan]{library}[/cyan].")


@app.command()
def report(
    library: Annotated[str, typer.Argument()],
) -> None:
    """Re-render the report from cached data (no network calls)."""
    import json

    from .config import lib_data_dir
    from .models import RepoDigest
    from .reporting import render
    from .summarization import summarize

    data_dir = lib_data_dir(library)
    top_dir = data_dir / "top_repos"
    if not top_dir.exists():
        console.print(f"[red]No cached digests found. Run `analyze {library}` first.[/red]")
        raise typer.Exit(1)

    digests = [
        RepoDigest.model_validate(json.loads(p.read_text()))
        for p in sorted(top_dir.glob("*.json"))
    ]
    if not digests:
        console.print(f"[red]No digest files in {top_dir}.[/red]")
        raise typer.Exit(1)

    synthesis = summarize(library, digests)
    out_path = render(library, digests, synthesis)
    console.print(f"Report re-rendered: [bold]{out_path}[/bold]")


def _print_summary_table(library: str, digests: list) -> None:
    table = Table(title=f"Top repos using {library}", show_lines=True)
    table.add_column("Repo", style="cyan", no_wrap=True)
    table.add_column("Stars", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Use-cases")

    for d in digests:
        table.add_row(
            d.full_name,
            str(d.stars),
            f"{d.score:.3f}",
            ", ".join(d.use_case_tags) or "—",
        )
    console.print(table)
