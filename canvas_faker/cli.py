"""CLI: python -m canvas_faker"""
import argparse
import sys

from .config import GenerationConfig, MessinessConfig
from .generate import generate_dataset


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a fake Canvas Data 2 dataset in SQLite."
    )
    parser.add_argument(
        "--out", "-o", default="cd2.db",
        help="Output SQLite path (default: cd2.db)"
    )
    parser.add_argument(
        "--seed", "-s", type=int, default=1234,
        help="RNG seed for reproducibility (default: 1234)"
    )
    parser.add_argument(
        "--scale", choices=["small", "medium", "large"], default="small",
        help="Dataset scale: small (~200 rows), medium (~4k rows), large (~40k rows)"
    )
    parser.add_argument(
        "--messiness", "-m", type=float, default=0.3,
        help="Messiness intensity 0.0–1.0 (default: 0.3)"
    )
    parser.add_argument(
        "--clean", action="store_true",
        help="Generate clean data (no messiness); overrides --messiness"
    )

    args = parser.parse_args()

    from .config import MessinessConfig

    cfg = GenerationConfig(
        seed=args.seed,
        scale=args.scale,
        messiness=MessinessConfig(
            intensity=0.0 if args.clean else args.messiness,
            enabled=not args.clean,
        ),
    )

    print(f"Generating Canvas Data 2 dataset...")
    print(f"  Output: {args.out}")
    print(f"  Scale: {args.scale}")
    print(f"  Seed: {args.seed}")
    print(f"  Messiness intensity: {cfg.messiness.intensity if cfg.messiness.enabled else 0.0}")
    print()

    try:
        conn = generate_dataset(cfg, args.out)
        conn.close()
        print()
        print(f"✓ Dataset generated: {args.out}")
        return 0
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
