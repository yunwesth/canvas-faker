"""Canvas-Faker: a Faker library for Canvas Data 2 (CD2)."""
from .config import GenerationConfig, MessinessConfig
from .generate import generate_dataset

__version__ = "0.1.0"
__all__ = ["generate_dataset", "GenerationConfig", "MessinessConfig"]
