"""MessinessEngine — applies real-world dirt to generated rows."""
from __future__ import annotations

import random
from datetime import timedelta
from typing import Any

from .config import MessinessConfig


class MessinessEngine:
    def __init__(self, cfg: MessinessConfig, rng: random.Random) -> None:
        self.cfg = cfg
        self.rng = rng

    def _roll(self, behavior: str, base: float) -> bool:
        return self.rng.random() < self.cfg.rate(behavior, base)

    # ------------------------------------------------------------------ #
    # Workflow state
    # ------------------------------------------------------------------ #

    def workflow_state(self, normal: str = "active") -> str:
        if self._roll("soft_delete", 0.05):
            return "deleted"
        return normal

    def enrollment_workflow_state(self) -> str:
        r = self.rng.random()
        if r < self.cfg.rate("dropped_enrollments", 0.12):
            return self.rng.choice(["completed", "rejected", "inactive"])
        return "active"

    # ------------------------------------------------------------------ #
    # Nullable fields
    # ------------------------------------------------------------------ #

    def maybe_null(self, value: Any, behavior: str = "nulls", base: float = 0.25) -> Any:
        """Return None instead of value at a rate driven by intensity."""
        if self._roll(behavior, base):
            return None
        return value

    # ------------------------------------------------------------------ #
    # SIS fields
    # ------------------------------------------------------------------ #

    def sis_source_id(self, value: str) -> str | None:
        return self.maybe_null(value, "missing_sis", 0.30)

    def sis_user_id(self, value: str) -> str | None:
        return self.maybe_null(value, "missing_sis", 0.40)

    # ------------------------------------------------------------------ #
    # Timestamps
    # ------------------------------------------------------------------ #

    def maybe_swap_timestamps(self, created: str, updated: str) -> tuple[str, str]:
        """Occasionally make updated_at < created_at (clock skew mess)."""
        if self._roll("timestamp_mess", 0.03):
            return updated, created
        return created, updated

    # ------------------------------------------------------------------ #
    # Submissions
    # ------------------------------------------------------------------ #

    def submission_status(self, due_at: str | None) -> dict:
        """Return dict of late/missing/excused + seconds_late."""
        late = False
        missing = False
        excused = False
        seconds_late = 0
        late_policy_status = None

        if self._roll("late_missing", 0.15):
            missing = True
            late_policy_status = "missing"
        elif self._roll("late_missing", 0.20):
            late = True
            seconds_late = self.rng.randint(60, 86400 * 5)
            late_policy_status = "late"
        elif self._roll("late_missing", 0.04):
            excused = True
            late_policy_status = None

        return {
            "late": int(late),
            "missing": int(missing),
            "excused": int(excused) if excused else None,
            "seconds_late": seconds_late,
            "late_policy_status": late_policy_status,
        }

    # ------------------------------------------------------------------ #
    # Scores
    # ------------------------------------------------------------------ #

    def score_and_grade(
        self, raw_score: float | None, max_pts: float, faker_inst: Any
    ) -> dict:
        """Return score, grade, published_score, published_grade, unposted versions."""
        if raw_score is None:
            return {
                "score": None, "grade": None,
                "published_score": None, "published_grade": None,
                "current_score": None, "final_score": 0.0,
                "current_grade": None, "final_grade": None,
                "unposted_current_score": None, "unposted_final_score": 0.0,
                "unposted_current_grade": None, "unposted_final_grade": None,
                "override_score": None, "override_grade": None,
            }

        pct = (raw_score / max_pts * 100) if max_pts else 0.0
        letter = faker_inst.letter_grade(pct)
        pub_score = raw_score
        pub_grade = letter

        # occasionally there's an unposted/mismatch
        unposted_score = pub_score
        unposted_grade = pub_grade
        override_score = None
        override_grade = None

        if self._roll("nulls", 0.08):
            unposted_score = faker_inst.realistic_score(max_pts, self.cfg.intensity)
            unposted_pct = (unposted_score / max_pts * 100) if max_pts else 0.0
            unposted_grade = faker_inst.letter_grade(unposted_pct)

        if self._roll("nulls", 0.03):
            override_score = round(raw_score + self.rng.uniform(-5, 5), 1)
            override_score = max(0.0, min(max_pts, override_score))
            ovr_pct = (override_score / max_pts * 100) if max_pts else 0.0
            override_grade = faker_inst.letter_grade(ovr_pct)

        return {
            "score": raw_score, "grade": letter,
            "published_score": pub_score, "published_grade": pub_grade,
            "current_score": pct, "final_score": pct,
            "current_grade": letter, "final_grade": letter,
            "unposted_current_score": unposted_score,
            "unposted_final_score": unposted_score,
            "unposted_current_grade": unposted_grade,
            "unposted_final_grade": unposted_grade,
            "override_score": override_score, "override_grade": override_grade,
        }

    # ------------------------------------------------------------------ #
    # Communication channels
    # ------------------------------------------------------------------ #

    def comm_channel_state(self) -> str:
        if self._roll("bounced_email", 0.08):
            return "bounced"
        return "active"

    def bounce_fields(self) -> dict:
        if self._roll("bounced_email", 0.08):
            count = self.rng.randint(1, 10)
            return {"bounce_count": count, "last_bounce_at": None}
        return {"bounce_count": 0, "last_bounce_at": None}

    # ------------------------------------------------------------------ #
    # User merges
    # ------------------------------------------------------------------ #

    def merged_user_id(self, user_ids: list[int]) -> int | None:
        if len(user_ids) > 2 and self._roll("merged_users", 0.04):
            return self.rng.choice(user_ids[:-1])
        return None

    def name_with_typo(self, name: str) -> str:
        """Occasionally introduce a casing/whitespace typo in a name."""
        if not self._roll("merged_users", 0.06):
            return name
        mutations = [
            lambda n: n.upper(),
            lambda n: n.lower(),
            lambda n: n + " ",
            lambda n: " " + n,
            lambda n: n.replace(" ", "  "),
        ]
        fn = self.rng.choice(mutations)
        return fn(name)

    # ------------------------------------------------------------------ #
    # Web log noise
    # ------------------------------------------------------------------ #

    def http_status(self, normal: int = 200) -> int:
        if self._roll("log_noise", 0.08):
            return self.rng.choice([400, 401, 403, 404, 422, 500, 502, 503])
        return normal

    def masquerade_user(self, user_ids: list[int], real_user_ids: list[int]) -> int | None:
        """Return a real_user_id (admin masquerading) or None."""
        if real_user_ids and self._roll("log_noise", 0.03):
            return self.rng.choice(real_user_ids)
        return None

    def user_agent(self, faker_ua: str) -> str:
        if self._roll("log_noise", 0.05):
            # truncated or malformed UA
            return faker_ua[:self.rng.randint(10, 40)]
        return faker_ua[:255]
