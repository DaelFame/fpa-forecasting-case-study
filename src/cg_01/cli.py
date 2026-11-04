from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_config
from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cg_01.cli",
        description="F1: inventario, capa canónica y Markdown de fuentes CompanyGame.",
    )
    parser.add_argument("--config", type=Path, default=None, help="Ruta a config/f1.toml.")
    parser.add_argument("--data-dir", type=Path, default=None, help="Directorio de datos de entrada.")
    parser.add_argument("--output", type=Path, default=None, help="Directorio de salida F1.")
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=None,
        help="Directorio de salida del Markdown generado.",
    )
    parser.add_argument(
        "--skip-markdown",
        action="store_true",
        help="No regenera la representación Markdown de los Excel.",
    )
    parser.add_argument("--quiet", action="store_true", help="No imprime el resumen final.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(
            args.config,
            data_dir=args.data_dir,
            output_dir=args.output,
            markdown_dir=args.markdown_output,
        )
        result = run_pipeline(config, export_markdown=not args.skip_markdown)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        severity = result.inventory["summary"]["anomalies_by_severity"]
        hashes = result.inventory["summary"]["all_hashes_unchanged"]
        print(
            "F1 completado: "
            f"{len(result.sources)} fuentes, "
            f"{result.raw_cell_count} celdas, "
            f"{len(result.observations)} observaciones, "
            f"{len(result.anomalies)} anomalías "
            f"(critical={severity['critical']}, high={severity['high']}, "
            f"medium={severity['medium']}, low={severity['low']}, info={severity['info']})."
        )
        print(f"Hashes sin cambios: {hashes}. Salida: {result.config.output_dir}")
        if not args.skip_markdown:
            summary = result.markdown["summary"]
            print(
                "Markdown: "
                f"{summary['workbooks_exported']} Excel, "
                f"{summary['captured_sources']} capturas, "
                f"{summary['sheets']} hojas, "
                f"{summary['indexed_cells']} celdas indexadas, "
                f"{summary['missing_cells']} no indexadas, "
                f"{summary['warnings']} advertencias. "
                f"Salida: {result.config.markdown_dir}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
