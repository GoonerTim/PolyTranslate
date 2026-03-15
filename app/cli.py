"""Command-line interface for PolyTranslate."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from app.config.languages import LANGUAGES
from app.config.settings import Settings
from app.core.batch_translator import BatchProgress, BatchTranslator
from app.core.file_processor import FileProcessor
from app.core.translator import Translator


def _load_settings(config_path: str | None) -> Settings:
    if config_path:
        return Settings(config_path=config_path)
    return Settings()


def _get_text(
    input_text: str | None,
    file: str | None,
) -> str:
    if file:
        path = Path(file)
        if not path.exists():
            click.echo(f"Error: file not found: {file}", err=True)
            sys.exit(1)
        return FileProcessor.process_file(path)

    if input_text:
        return input_text

    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    click.echo("Error: provide text as argument, --file, or pipe via stdin", err=True)
    sys.exit(1)


def _resolve_params(
    source: str | None,
    target: str | None,
    chunk_size: int | None,
    max_workers: int | None,
    settings: Settings,
) -> tuple[str, str, int, int]:
    src = source or settings.get_source_language()
    tgt = target or settings.get_target_language()
    cs = chunk_size or settings.get_chunk_size()
    mw = max_workers or settings.get_max_workers()
    return src, tgt, cs, mw


def _resolve_services(
    all_services: bool,
    services: tuple[str, ...] | None,
    translator: Translator,
    settings: Settings,
) -> list[str]:
    available = translator.get_available_services()
    if not available:
        click.echo("Error: no translation services configured", err=True)
        sys.exit(1)

    if all_services:
        return available
    if services:
        svc_list = list(services)
        invalid = [s for s in svc_list if s not in available]
        if invalid:
            click.echo(f"Error: unavailable services: {', '.join(invalid)}", err=True)
            click.echo(f"Available: {', '.join(available)}", err=True)
            sys.exit(1)
        return svc_list

    configured = settings.get_selected_services()
    result = [s for s in configured if s in available]
    return result if result else available[:1]


def _progress_callback(completed: int, total: int) -> None:
    pct = int(completed / total * 100) if total else 100
    bar_len = 30
    filled = int(bar_len * completed / total) if total else bar_len
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"\r  [{bar}] {pct}% ({completed}/{total})", end="", flush=True, file=sys.stderr)
    if completed == total:
        print(file=sys.stderr)


def _format_results(results: dict[str, str], fmt: str) -> str:
    if fmt == "json":
        return json.dumps(results, ensure_ascii=False, indent=2)

    if len(results) == 1:
        return next(iter(results.values()))

    parts: list[str] = []
    for service, translation in results.items():
        parts.append(f"=== {service.upper()} ===")
        parts.append(translation)
        parts.append("")
    return "\n".join(parts).rstrip()


@click.group(name="polytranslate")
def cli() -> None:
    """PolyTranslate — translate text and files using multiple services."""


@cli.command(name="translate")
@click.argument("input", required=False, default=None)
@click.option("-f", "--file", "file_path", type=str, default=None, help="Input file path")
@click.option("-d", "--directory", type=str, default=None, help="Translate all files in directory")
@click.option("-o", "--output", type=str, default=None, help="Output file path (default: stdout)")
@click.option("--output-dir", type=str, default=None, help="Output directory for batch translation")
@click.option(
    "--extensions",
    type=str,
    multiple=True,
    help="File extensions to process in batch mode (default: .rpy)",
)
@click.option("--no-recursive", is_flag=True, default=False, help="Do not search subdirectories")
@click.option("--service", type=str, default=None, help="Service for output files in batch mode")
@click.option("-s", "--source", type=str, default=None, help="Source language code")
@click.option("-t", "--target", type=str, default=None, help="Target language code")
@click.option("--services", type=str, multiple=True, help="Translation services to use")
@click.option("--all-services", is_flag=True, default=False, help="Use all available services")
@click.option("--chunk-size", type=int, default=None, help="Chunk size for splitting text")
@click.option("--max-workers", type=int, default=None, help="Max parallel workers")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.option(
    "--export",
    type=str,
    default=None,
    help="Export results to DOCX/PDF/XLIFF (e.g. --export results.docx)",
)
@click.option("--stream", is_flag=True, default=False, help="Stream LLM output token-by-token")
@click.option("--config", "config_path", type=str, default=None, help="Path to config.json")
def cmd_translate(
    input: str | None,
    file_path: str | None,
    directory: str | None,
    output: str | None,
    output_dir: str | None,
    extensions: tuple[str, ...],
    no_recursive: bool,
    service: str | None,
    source: str | None,
    target: str | None,
    services: tuple[str, ...],
    all_services: bool,
    chunk_size: int | None,
    max_workers: int | None,
    fmt: str,
    export: str | None,
    stream: bool,
    config_path: str | None,
) -> None:
    """Translate text or file."""
    settings = _load_settings(config_path)
    translator = Translator(settings)

    if directory:
        return _cmd_translate_directory(
            directory=directory,
            output_dir=output_dir,
            extensions=extensions,
            no_recursive=no_recursive,
            service=service,
            source=source,
            target=target,
            services=services,
            all_services=all_services,
            chunk_size=chunk_size,
            max_workers=max_workers,
            fmt=fmt,
            settings=settings,
            translator=translator,
        )

    text = _get_text(input, file_path)
    src, tgt, cs, mw = _resolve_params(source, target, chunk_size, max_workers, settings)
    svc_list = _resolve_services(all_services, services or None, translator, settings)

    if src == "auto":
        detected = translator.detect_language(text)
        if detected:
            src = detected
            click.echo(f"Detected language: {LANGUAGES.get(src, src)}", err=True)

    is_file = bool(file_path)
    if is_file:
        src_name = LANGUAGES.get(src, src) if src else "auto"
        tgt_name = LANGUAGES.get(tgt, tgt) if tgt else tgt
        click.echo(f"Translating: {file_path}", err=True)
        click.echo(f"  {src_name} → {tgt_name} | services: {', '.join(svc_list)}", err=True)

    on_token_map: dict[str, Any] | None = None
    if stream:
        if len(svc_list) > 1:
            click.echo("Streaming mode: showing tokens for each service tab", err=True)

        def _make_token_cb(svc_name: str) -> Any:
            def _cb(token: str) -> None:
                print(token, end="", flush=True, file=sys.stderr)

            return _cb

        on_token_map = {svc: _make_token_cb(svc) for svc in svc_list}

    results = translator.translate_parallel(
        text=text,
        source_lang=src,
        target_lang=tgt,
        services=svc_list,
        chunk_size=cs,
        max_workers=mw,
        progress_callback=None if stream else _progress_callback,
        on_token=on_token_map,
    )

    if stream:
        print(file=sys.stderr)  # newline after streaming output

    translator.cache.save()

    formatted = _format_results(results, fmt)

    if output:
        Path(output).write_text(formatted, encoding="utf-8")
        click.echo(f"Saved to {output}", err=True)
    else:
        click.echo(formatted)

    if export:
        from app.core.exporter import TranslationExporter

        file_name = Path(file_path).name if file_path else ""
        export_path = TranslationExporter.export(
            original_text=text,
            translations=results,
            source_lang=src,
            target_lang=tgt,
            output_path=export,
            file_name=file_name,
        )
        click.echo(f"Exported to {export_path}", err=True)

    if is_file:
        click.echo("Done.", err=True)


def _cmd_translate_directory(
    *,
    directory: str,
    output_dir: str | None,
    extensions: tuple[str, ...],
    no_recursive: bool,
    service: str | None,
    source: str | None,
    target: str | None,
    services: tuple[str, ...],
    all_services: bool,
    chunk_size: int | None,
    max_workers: int | None,
    fmt: str,
    settings: Settings,
    translator: Translator,
) -> None:
    dir_path = Path(directory)
    if not dir_path.is_dir():
        click.echo(f"Error: directory not found: {directory}", err=True)
        sys.exit(1)

    src, tgt, cs, mw = _resolve_params(source, target, chunk_size, max_workers, settings)
    svc_list = _resolve_services(all_services, services or None, translator, settings)

    ext_set = {f".{e.lstrip('.')}" for e in extensions} if extensions else None
    out_dir = Path(output_dir) if output_dir else None
    recursive = not no_recursive

    batch = BatchTranslator(translator)
    files = batch.find_files(dir_path, ext_set, recursive)

    if not files:
        ext_str = ", ".join(ext_set) if ext_set else ".rpy"
        click.echo(f"No {ext_str} files found in {directory}", err=True)
        sys.exit(1)

    click.echo(f"Translating folder: {directory}", err=True)
    click.echo(f"Found {len(files)} file(s)\n", err=True)

    def batch_progress(progress: BatchProgress) -> None:
        idx = progress.current_file_index + 1
        total = progress.total_files
        name = progress.current_file_name
        if progress.file_completed:
            click.echo("  ✓ Done\n", err=True)
        else:
            click.echo(f"[{idx}/{total}] {name}", err=True)

    results = batch.translate_folder(
        directory=dir_path,
        source_lang=src,
        target_lang=tgt,
        services=svc_list,
        extensions=ext_set,
        output_dir=out_dir,
        service_name=service,
        chunk_size=cs,
        max_workers=mw,
        recursive=recursive,
        progress_callback=batch_progress,
    )

    translator.cache.save()

    succeeded = sum(1 for r in results if r.success and not r.error)
    skipped = sum(1 for r in results if r.success and r.error)
    failed = sum(1 for r in results if not r.success)

    click.echo(
        f"\nResults: {succeeded} translated, {skipped} skipped, {failed} failed",
        err=True,
    )

    if fmt == "json":
        json_results = []
        for r in results:
            json_results.append(
                {
                    "source": str(r.source_path),
                    "output": str(r.output_path) if r.output_path else None,
                    "success": r.success,
                    "error": r.error,
                }
            )
        click.echo(json.dumps(json_results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            if not r.success:
                click.echo(f"  FAILED: {r.source_path} — {r.error}", err=True)
            elif r.output_path:
                click.echo(f"  {r.output_path}")


@cli.command(name="services")
@click.option("--config", "config_path", type=str, default=None, help="Path to config.json")
def cmd_services(config_path: str | None) -> None:
    """List available translation services."""
    settings = _load_settings(config_path)
    translator = Translator(settings)

    all_svcs = translator.services
    available = translator.get_available_services()
    selected = settings.get_selected_services()

    for name, service in all_svcs.items():
        status = "+" if name in available else "-"
        sel = " [selected]" if name in selected else ""
        click.echo(f"  {status} {name:20s} {service.get_name()}{sel}")


@cli.command(name="languages")
def cmd_languages() -> None:
    """List supported languages."""
    for code, name in LANGUAGES.items():
        if code == "auto":
            continue
        click.echo(f"  {code:6s} {name}")


@cli.command(name="detect")
@click.argument("input", required=False, default=None)
@click.option("-f", "--file", "file_path", type=str, default=None, help="Input file path")
def cmd_detect(input: str | None, file_path: str | None) -> None:
    """Detect language of text."""
    text = _get_text(input, file_path)

    from app.core.language_detector import LanguageDetector

    detector = LanguageDetector()
    lang = detector.detect(text)
    if lang:
        name = LANGUAGES.get(lang, lang)
        click.echo(f"{lang} ({name})")
    else:
        click.echo("Could not detect language", err=True)
        sys.exit(1)


@cli.group(name="cache")
def cache_group() -> None:
    """Manage translation cache (export/import TMX)."""


@cache_group.command(name="export-tmx")
@click.argument("output")
@click.option("--config", "config_path", type=str, default=None, help="Path to config.json")
def cmd_cache_export(output: str, config_path: str | None) -> None:
    """Export cache to TMX file."""
    settings = _load_settings(config_path)

    from app.utils.cache import TranslationCache

    cache = TranslationCache(
        cache_path=settings.get("cache_path", "cache.json"),
        enabled=True,
    )
    if len(cache) == 0:
        click.echo("Cache is empty, nothing to export.", err=True)
        sys.exit(1)
    result = cache.export_tmx(output)
    click.echo(f"Exported {len(cache)} entries to {result}", err=True)


@cache_group.command(name="import-tmx")
@click.argument("input")
@click.option("--config", "config_path", type=str, default=None, help="Path to config.json")
def cmd_cache_import(input: str, config_path: str | None) -> None:
    """Import TMX file into cache."""
    input_path = Path(input)
    if not input_path.exists():
        click.echo(f"Error: file not found: {input}", err=True)
        sys.exit(1)

    settings = _load_settings(config_path)

    from app.utils.cache import TranslationCache

    cache = TranslationCache(
        cache_path=settings.get("cache_path", "cache.json"),
        enabled=True,
    )
    count = cache.import_tmx(input_path)
    cache.save()
    click.echo(f"Imported {count} entries from {input_path}", err=True)


@cli.command(name="config")
@click.option("--show", is_flag=True, default=False, help="Show current config (default action)")
@click.option("--set", "set_pair", nargs=2, type=str, default=None, help="Set a config value")
@click.option("--set-key", "set_key_pair", nargs=2, type=str, default=None, help="Set an API key")
@click.option("--config", "config_path", type=str, default=None, help="Path to config.json")
def cmd_config(
    show: bool,
    set_pair: tuple[str, str] | None,
    set_key_pair: tuple[str, str] | None,
    config_path: str | None,
) -> None:
    """Show or update configuration."""
    settings = _load_settings(config_path)

    if set_pair:
        key, value = set_pair
        # Try to parse as JSON for non-string types
        try:
            parsed: Any = json.loads(value)
        except json.JSONDecodeError:
            parsed = value
        settings.set(key, parsed)
        settings.save()
        click.echo(f"Set {key} = {parsed}")
        return

    if set_key_pair:
        svc, key = set_key_pair
        settings.set_api_key(svc, key)
        settings.save()
        click.echo(f"API key set for {svc}")
        return

    # Default: show config
    config = settings.to_dict()
    # Mask API keys
    if "api_keys" in config:
        masked = {}
        for svc, key in config["api_keys"].items():
            if key:
                masked[svc] = key[:4] + "..." + key[-4:] if len(key) > 8 else "****"
            else:
                masked[svc] = "(not set)"
        config["api_keys"] = masked
    click.echo(json.dumps(config, indent=2, ensure_ascii=False))


# --- Backward-compatible entry point ---

# Command aliases mapping
_ALIASES: dict[str, str] = {
    "t": "translate",
    "s": "services",
    "l": "languages",
    "d": "detect",
    "c": "config",
}


def run_cli(argv: list[str] | None = None) -> None:
    """Entry point for CLI. Supports aliases and backward compatibility."""
    args = argv if argv is not None else sys.argv[1:]

    # Resolve command aliases
    if args and args[0] in _ALIASES:
        args = [_ALIASES[args[0]]] + list(args[1:])

    # Handle empty args — show help and exit
    if not args:
        ctx = click.Context(cli)
        click.echo(cli.get_help(ctx))
        sys.exit(0)

    cli(args, standalone_mode=False)
