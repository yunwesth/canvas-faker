"""Configuration for a generation run: volume + messiness knobs."""
from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass
class MessinessConfig:
    """Controls real-world messiness. Every behavior scales with ``intensity``
    (0.0 = pristine data, 1.0 = maximally messy) and can be toggled off.

    Each behavior has a base rate; the effective probability is
    ``base_rate * intensity`` (when enabled)."""

    intensity: float = 0.3
    enabled: bool = True

    soft_delete: bool = True             # workflow_state = 'deleted'
    nulls: bool = True                   # drop optional fields
    late_missing: bool = True            # late / missing / excused submissions
    bounced_email: bool = True           # bounced communication_channels
    merged_users: bool = True            # merged_into_user_id + near-duplicate names
    dropped_enrollments: bool = True     # concluded / rejected / deleted enrollments
    timestamp_mess: bool = True          # tz spread, updated_at < created_at
    log_noise: bool = True               # 4xx/5xx, masquerading, truncated UA
    missing_sis: bool = True             # partial SIS linkage

    def rate(self, behavior: str, base: float) -> float:
        """Effective probability for a behavior, 0 when disabled."""
        if not self.enabled or not getattr(self, behavior, False):
            return 0.0
        return max(0.0, min(1.0, base * self.intensity))


@dataclass
class GenerationConfig:
    seed: int = 1234
    scale: str = "small"

    # Volume knobs (filled from the scale preset when left as None).
    n_root_accounts: int | None = None
    n_sub_accounts: int | None = None
    n_terms: int | None = None
    n_courses: int | None = None
    students_per_course: int | None = None
    teachers_per_course: int | None = None
    sections_per_course: int | None = None
    assignments_per_course: int | None = None
    quizzes_per_course: int | None = None
    discussions_per_course: int | None = None
    modules_per_course: int | None = None
    web_log_days: int | None = None
    logs_per_student_day: int | None = None

    messiness: MessinessConfig = field(default_factory=MessinessConfig)

    def resolved(self) -> "GenerationConfig":
        """Return a copy with all None volume knobs filled from the scale preset."""
        preset = SCALE_PRESETS.get(self.scale, SCALE_PRESETS["small"])
        overrides = {
            k: (getattr(self, k) if getattr(self, k) is not None else v)
            for k, v in preset.items()
        }
        return replace(self, **overrides)


SCALE_PRESETS: dict[str, dict[str, int]] = {
    "small": dict(
        n_root_accounts=1, n_sub_accounts=3, n_terms=2, n_courses=8,
        students_per_course=25, teachers_per_course=1, sections_per_course=2,
        assignments_per_course=6, quizzes_per_course=2, discussions_per_course=2,
        modules_per_course=3, web_log_days=14, logs_per_student_day=3),
    "medium": dict(
        n_root_accounts=1, n_sub_accounts=6, n_terms=4, n_courses=40,
        students_per_course=40, teachers_per_course=2, sections_per_course=3,
        assignments_per_course=10, quizzes_per_course=4, discussions_per_course=3,
        modules_per_course=5, web_log_days=30, logs_per_student_day=4),
    "large": dict(
        n_root_accounts=2, n_sub_accounts=12, n_terms=6, n_courses=200,
        students_per_course=60, teachers_per_course=2, sections_per_course=4,
        assignments_per_course=14, quizzes_per_course=6, discussions_per_course=4,
        modules_per_course=6, web_log_days=30, logs_per_student_day=5),
}
