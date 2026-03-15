"""Command-line interface for PolyTranslate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from app.config.languages import LANGUAGES
from app.config.settings import Settings
from app.core.batch_translator import BatchProgress, BatchTranslator
from app.core.file_processor import FileProcessor
from app.core.translator import Translator


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="polytranslate",
        description="PolyTranslate — translate text and files using multiple services",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- translate ---
    tr = subparsers.add_parser("translate", aliases=["t"], help="Translate text or file")
    tr.add_argument("input", nargs="?", help="Text to translate (or use --file)")
    tr.add_argument("-f", "--file", type=str, help="Input file path")
    tr.add_argument("-d", "--directory", type=str, help="Translate all files in directory")
    tr.add_argument("-o", "--output", type=str, help="Output file path (default: stdout)")
    tr.add_argument("--output-dir", type=str, help="Output directory for batch translation")
    tr.add_argument(
        "--extensions",
        type=str,
        nargs="+",
        help="File extensions to process in batch mode (default: .rpy)",
    )
    tr.add_argument("--no-recursive", action="store_true", help="Do not search subdirectories")
    tr.add_argument(
        "--service",
        type=str,
        help="Service to use for output files in batch mode",
    )
    tr.add_argument(
        "-s",
        "--source",
        type=str,
        default=None,
        help="Source language code (default: from config or auto)",
    )
    tr.add_argument(
        "-t", "--target", type=str, default=None, help="Target language code (default: from config)"
    )
    tr.add_argument(
        "--services",
        type=str,
        nargs="+",
        help="Translation services to use (default: from config)",
    )
    tr.add_argument("--all-services", action="store_true", help="Use all available services")
    tr.add_argument("--chunk-size", type=int, default=None, help="Chunk size for splitting text")
    tr.add_argument("--max-workers", type=int, default=None, help="Max parallel workers")
    tr.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format (default: text)"
    )
    tr.add_argument(
        "--export",
        type=str,
        default=None,
        help="Export results to DOCX/PDF/XLIFF (e.g. --export results.docx)",
    )
    tr.add_argument("--config", type=str, default=None, help="Path to config.json")

    # --- services ---
    svc = subparsers.add_parser(
        "services", aliases=["s"], help="List available translation services"
    )
    svc.add_argument("--config", type=str, default=None, help="Path to config.json")

    # --- languages ---
    subparsers.add_parser("languages", aliases=["l"], help="List supported languages")

    # --- detect ---
    det = subparsers.add_parser("detect", aliases=["d"], help="Detect language of text")
    det.add_argument("input", nargs="?", help="Text to detect (or use --file)")
    det.add_argument("-f", "--file", type=str, help="Input file path")

    # --- cache ---
    ca = subparsers.add_parser("cache", help="Manage translation cache (export/import TMX)")
    ca_sub = ca.add_subparsers(dest="cache_action", help="Cache actions")
    ca_export = ca_sub.add_parser("export-tmx", help="Export cache to TMX file")
    ca_export.add_argument("output", type=str, help="Output TMX file path")
    ca_export.add_argument("--config", type=str, default=None, help="Path to config.json")
    ca_import = ca_sub.add_parser("import-tmx", help="Import TMX file into cache")
    ca_import.add_argument("input", type=str, help="Input TMX file path")
    ca_import.add_argument("--config", type=str, default=None, help="Path to config.json")

    # --- config ---
    cfg = subparsers.add_parser("config", aliases=["c"], help="Show or update configuration")
    cfg.add_argument("--show", action="store_true", help="Show current config (default action)")
    cfg.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), help="Set a config value")
    cfg.add_argument("--set-key", nargs=2, metavar=("SERVICE", "KEY"), help="Set an API key")
    cfg.add_argument("--config", type=str, default=None, help="Path to config.json")

    return parser


def _load_settings(config_path: str | None) -> Settings:
    if config_path:
        return Settings(config_path=config_path)
    return Settings()


def _get_text(args: argparse.Namespace) -> str:
    if getattr(args, "file", None):
        path = Path(args.file)
        if not path.exists():
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        return FileProcessor.process_file(path)

    if getattr(args, "input", None):
        return args.input

    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    print("Error: provide text as argument, --file, or pipe via stdin", file=sys.stderr)
    sys.exit(1)


def _resolve_params(args: argparse.Namespace, settings: Settings) -> tuple[str, str, int, int]:
    source = args.source or settings.get_source_language()
    target = args.target or settings.get_target_language()
    chunk_size = args.chunk_size or settings.get_chunk_size()
    max_workers = args.max_workers or settings.get_max_workers()
    return source, target, chunk_size, max_workers


def _resolve_services(
    args: argparse.Namespace, translator: Translator, settings: Settings
) -> list[str]:
    available = translator.get_available_services()
    if not available:
        print("Error: no translation services configured", file=sys.stderr)
        sys.exit(1)

    if args.all_services:
        return available
    if args.services:
        invalid = [s for s in args.services if s not in available]
        if invalid:
            print(f"Error: unavailable services: {', '.join(invalid)}", file=sys.stderr)
            print(f"Available: {', '.join(available)}", file=sys.stderr)
            sys.exit(1)
        return args.services

    configured = settings.get_selected_services()
    services = [s for s in configured if s in available]
    return services if services else available[:1]


def _progress_callback(completed: int, total: int) -> None:
    pct = int(completed / total * 100) if total else 100
    bar_len = 30
    filled = int(bar_len * completed / total) if total else bar_len
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"\r  [{bar}] {pct}% ({completed}/{total})", end="", flush=True, file=sys.stderr)
    if completed == total:
        print(file=sys.stderr)


def cmd_translate(args: argparse.Namespace) -> None:
    settings = _load_settings(getattr(args, "config", None))
    translator = Translator(settings)

    if getattr(args, "directory", None):
        return _cmd_translate_directory(args, settings, translator)

    text = _get_text(args)
    source, target, chunk_size, max_workers = _resolve_params(args, settings)
    services = _resolve_services(args, translator, settings)

    if source == "auto":
        detected = translator.detect_language(text)
        if detected:
            source = detected
            print(f"Detected language: {LANGUAGES.get(source, source)}", file=sys.stderr)

    is_file = bool(getattr(args, "file", None))
    if is_file:
        src_name = LANGUAGES.get(source, source) if source else "auto"
        tgt_name = LANGUAGES.get(target, target) if target else target
        print(f"Translating: {args.file}", file=sys.stderr)
        print(f"  {src_name} → {tgt_name} | services: {', '.join(services)}", file=sys.stderr)

    results = translator.translate_parallel(
        text=text,
        source_lang=source,
        target_lang=target,
        services=services,
        chunk_size=chunk_size,
        max_workers=max_workers,
        progress_callback=_progress_callback,
    )

    translator.cache.save()

    output = _format_results(results, args.format)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        print(output)

    if getattr(args, "export", None):
        from app.core.exporter import TranslationExporter

        file_name = Path(args.file).name if getattr(args, "file", None) else ""
        export_path = TranslationExporter.export(
            original_text=text,
            translations=results,
            source_lang=source,
            target_lang=target,
            output_path=args.export,
            file_name=file_name,
        )
        print(f"Exported to {export_path}", file=sys.stderr)

    if is_file:
        print("Done.", file=sys.stderr)


def _cmd_translate_directory(
    args: argparse.Namespace,
    settings: Settings,
    translator: Translator,
) -> None:
    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"Error: directory not found: {args.directory}", file=sys.stderr)
        sys.exit(1)

    source, target, chunk_size, max_workers = _resolve_params(args, settings)
    services = _resolve_services(args, translator, settings)

    extensions = {f".{e.lstrip('.')}" for e in args.extensions} if args.extensions else None
    output_dir = Path(args.output_dir) if getattr(args, "output_dir", None) else None
    recursive = not getattr(args, "no_recursive", False)
    service_name = getattr(args, "service", None)

    batch = BatchTranslator(translator)
    files = batch.find_files(directory, extensions, recursive)

    if not files:
        ext_str = ", ".join(extensions) if extensions else ".rpy"
        print(f"No {ext_str} files found in {directory}", file=sys.stderr)
        sys.exit(1)

    print(f"Translating folder: {directory}", file=sys.stderr)
    print(f"Found {len(files)} file(s)\n", file=sys.stderr)

    def batch_progress(progress: BatchProgress) -> None:
        idx = progress.current_file_index + 1
        total = progress.total_files
        name = progress.current_file_name
        if progress.file_completed:
            print("  ✓ Done\n", file=sys.stderr)
        else:
            print(f"[{idx}/{total}] {name}", file=sys.stderr)

    results = batch.translate_folder(
        directory=directory,
        source_lang=source,
        target_lang=target,
        services=services,
        extensions=extensions,
        output_dir=output_dir,
        service_name=service_name,
        chunk_size=chunk_size,
        max_workers=max_workers,
        recursive=recursive,
        progress_callback=batch_progress,
    )

    translator.cache.save()

    succeeded = sum(1 for r in results if r.success and not r.error)
    skipped = sum(1 for r in results if r.success and r.error)
    failed = sum(1 for r in results if not r.success)

    print(f"\nResults: {succeeded} translated, {skipped} skipped, {failed} failed", file=sys.stderr)

    if args.format == "json":
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
        print(json.dumps(json_results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            if not r.success:
                print(f"  FAILED: {r.source_path} — {r.error}", file=sys.stderr)
            elif r.output_path:
                print(f"  {r.output_path}")


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


def cmd_services(args: argparse.Namespace) -> None:
    settings = _load_settings(getattr(args, "config", None))
    translator = Translator(settings)

    all_services = translator.services
    available = translator.get_available_services()
    selected = settings.get_selected_services()

    for name, service in all_services.items():
        status = "+" if name in available else "-"
        sel = " [selected]" if name in selected else ""
        print(f"  {status} {name:20s} {service.get_name()}{sel}")


def cmd_languages(_args: argparse.Namespace) -> None:
    for code, name in LANGUAGES.items():
        if code == "auto":
            continue
        print(f"  {code:6s} {name}")


def cmd_detect(args: argparse.Namespace) -> None:
    text = _get_text(args)

    from app.core.language_detector import LanguageDetector

    detector = LanguageDetector()
    lang = detector.detect(text)
    if lang:
        name = LANGUAGES.get(lang, lang)
        print(f"{lang} ({name})")
    else:
        print("Could not detect language", file=sys.stderr)
        sys.exit(1)


def cmd_cache(args: argparse.Namespace) -> None:
    settings = _load_settings(getattr(args, "config", None))

    if args.cache_action == "export-tmx":
        from app.utils.cache import TranslationCache

        cache = TranslationCache(
            cache_path=settings.get("cache_path", "cache.json"),
            enabled=True,
        )
        if len(cache) == 0:
            print("Cache is empty, nothing to export.", file=sys.stderr)
            sys.exit(1)
        output = cache.export_tmx(args.output)
        print(f"Exported {len(cache)} entries to {output}", file=sys.stderr)

    elif args.cache_action == "import-tmx":
        from app.utils.cache import TranslationCache

        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        cache = TranslationCache(
            cache_path=settings.get("cache_path", "cache.json"),
            enabled=True,
        )
        count = cache.import_tmx(input_path)
        cache.save()
        print(f"Imported {count} entries from {input_path}", file=sys.stderr)

    else:
        print("Usage: polytranslate cache {export-tmx,import-tmx}", file=sys.stderr)
        sys.exit(1)


def cmd_config(args: argparse.Namespace) -> None:
    settings = _load_settings(getattr(args, "config", None))

    if args.set:
        key, value = args.set
        # Try to parse as JSON for non-string types
        try:
            parsed: Any = json.loads(value)
        except json.JSONDecodeError:
            parsed = value
        settings.set(key, parsed)
        settings.save()
        print(f"Set {key} = {parsed}")
        return

    if args.set_key:
        service, key = args.set_key
        settings.set_api_key(service, key)
        settings.save()
        print(f"API key set for {service}")
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
    print(json.dumps(config, indent=2, ensure_ascii=False))


def run_cli(argv: list[str] | None = None) -> None:
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    commands = {
        "translate": cmd_translate,
        "t": cmd_translate,
        "services": cmd_services,
        "s": cmd_services,
        "languages": cmd_languages,
        "l": cmd_languages,
        "detect": cmd_detect,
        "d": cmd_detect,
        "cache": cmd_cache,
        "config": cmd_config,
        "c": cmd_config,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
