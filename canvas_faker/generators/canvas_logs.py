"""Generator for canvas_logs namespace (web_logs table)."""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from faker import Faker

from ..config import GenerationConfig
from ..ids import IdAllocator, Registry, new_uuid
from ..messiness import MessinessEngine

UTC = timezone.utc

CONTROLLERS = [
    "courses", "assignments", "submissions", "quizzes", "discussion_topics",
    "users", "grades", "modules", "pages", "files", "announcements",
]
ACTIONS = ["show", "index", "create", "update", "destroy", "submit"]
HTTP_VERSIONS = ["HTTP/1.1", "HTTP/2.0"]


def _dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def generate(
    cfg: GenerationConfig,
    fake: Faker,
    ids: IdAllocator,
    reg: Registry,
    mess: MessinessEngine,
) -> dict[str, list[dict]]:
    rng = mess.rng
    now = datetime(2025, 8, 1, tzinfo=UTC)

    user_ids = reg.ids("canvas.users")
    course_ids = reg.ids("canvas.courses")
    quiz_ids = reg.ids("canvas.quizzes")
    disc_ids = reg.ids("canvas.discussion_topics")
    conv_ids = reg.ids("canvas.conversations")
    assign_ids = reg.ids("canvas.assignments")
    dk_ids = reg.ids("canvas.developer_keys")
    teacher_upper = max(1, len(user_ids) // 5)
    teacher_ids = user_ids[-teacher_upper:]  # teachers registered later = higher ids

    rows: list[dict] = []

    for day_offset in range(cfg.web_log_days):
        day_start = now - timedelta(days=cfg.web_log_days - day_offset)
        for uid in user_ids:
            n_logs = rng.randint(1, cfg.logs_per_student_day + 2)
            for _ in range(n_logs):
                ts = day_start + timedelta(seconds=rng.randint(0, 86399))
                controller = rng.choice(CONTROLLERS)
                action = rng.choice(ACTIONS)
                course_id = rng.choice(course_ids) if course_ids and rng.random() < 0.8 else None
                quiz_id = rng.choice(quiz_ids) if quiz_ids and controller == "quizzes" else None
                disc_id = rng.choice(disc_ids) if disc_ids and controller == "discussion_topics" else None
                conv_id = rng.choice(conv_ids) if conv_ids and controller == "conversations" else None
                assign_id = rng.choice(assign_ids) if assign_ids and controller == "assignments" else None

                http_status = mess.http_status(200)
                real_user_id = mess.masquerade_user(user_ids, teacher_ids)
                ua = mess.user_agent(fake.user_agent())

                url_path = f"/courses/{course_id}/{controller}" if course_id else f"/{controller}"
                rows.append({
                    "id": new_uuid(), "timestamp": _dt(ts),
                    "user_id": uid, "real_user_id": real_user_id,
                    "course_id": course_id, "quiz_id": quiz_id,
                    "discussion_id": disc_id, "conversation_id": conv_id,
                    "assignment_id": assign_id, "url": url_path,
                    "http_method": rng.choice(["GET", "GET", "GET", "POST", "PUT"]),
                    "http_status": http_status, "http_version": rng.choice(HTTP_VERSIONS),
                    "remote_ip": fake.ipv4() if rng.random() < 0.9 else fake.ipv6(),
                    "interaction_micros": rng.randint(5000, 2000000),
                    "web_application_controller": controller,
                    "web_application_action": action,
                    "web_application_context_type": "Course" if course_id else None,
                    "web_application_context_id": course_id,
                    "session_id": new_uuid() if rng.random() < 0.8 else None,
                    "developer_key_id": rng.choice(dk_ids) if dk_ids and rng.random() < 0.05 else None,
                    "participated": rng.random() < 0.3,
                    "user_agent": ua,
                })

    return {"web_logs": rows}
