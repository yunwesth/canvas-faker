"""Generator for new_quizzes namespace."""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone

from faker import Faker

from ..config import GenerationConfig
from ..ids import IdAllocator, Registry
from ..messiness import MessinessEngine

UTC = timezone.utc


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

    rows: dict[str, list[dict]] = {
        "quizzes": [], "quiz_questions": [], "quiz_submissions": [],
        "assignments": [], "assignment_overrides": [], "assignment_override_students": [],
        "assessment_question_banks": [], "assessment_questions": [],
    }

    # Question banks
    qb_ids = []
    for _ in range(2):
        qb_id = ids.next("new_quizzes_assessment_question_banks")
        created = _dt(now - timedelta(days=200))
        rows["assessment_question_banks"].append({
            "id": qb_id, "created_at": created, "updated_at": created,
            "deleted_at": None, "workflow_state": "active",
            "migration_id": None, "title": f"Question Bank {len(qb_ids)+1}",
        })
        qb_ids.append(qb_id)
        reg.register("new_quizzes.assessment_question_banks", qb_id)

    # Assessment questions
    for qb_id in qb_ids:
        for n in range(5):
            rows["assessment_questions"].append({
                "id": ids.next("new_quizzes_assessment_questions"),
                "name": f"Question {n+1}", "created_at": _dt(now - timedelta(days=200)),
                "updated_at": _dt(now - timedelta(days=200)), "deleted_at": None,
                "workflow_state": "active", "context_id": None, "context_type": None,
                "migration_id": None, "assessment_question_bank_id": qb_id,
                "question_data": json.dumps({"question_type": "multiple_choice_question", "points_possible": 1}),
                "position": n, "item_id": None,
            })

    # New Quizzes assignments + quizzes
    canvas_courses = reg.ids("canvas.courses")
    for _ in range(max(5, cfg.n_courses // 2)):
        aid = ids.next("new_quizzes_assignments")
        created = _dt(now - timedelta(days=100))
        cid = rng.choice(canvas_courses) if canvas_courses else rng.randint(1, 1000)
        rows["assignments"].append({
            "id": aid, "integration_id": None, "lti_context_id": None,
            "created_at": created, "updated_at": created, "workflow_state": "published",
            "due_at": _dt(now + timedelta(days=30)), "unlock_at": _dt(now - timedelta(days=7)),
            "lock_at": _dt(now + timedelta(days=37)), "points_possible": rng.choice([10, 25, 50, 100]),
            "grading_type": "points", "submission_types": ["online_text_entry", "online_upload"],
            "assignment_group_id": None, "grading_standard_id": None,
            "peer_reviews": False, "automatic_peer_reviews": False,
            "moderated_grading": False, "anonymous_grading": False,
            "omit_from_final_grade": False, "only_visible_to_overrides": False,
            "context_id": cid, "context_type": "Course", "allowed_attempts": 1,
            "position": None, "title": f"Assignment {len(rows['assignments'])+1}",
            "has_sub_assignments": None, "parent_assignment_id": None,
        })
        reg.register("new_quizzes.assignments", aid)

        # New Quizzes quiz linked to this assignment
        qid = ids.next("new_quizzes_quizzes")
        rows["quizzes"].append({
            "id": qid, "created_at": created, "updated_at": created,
            "due_at": _dt(now + timedelta(days=30)), "unlock_at": _dt(now - timedelta(days=7)),
            "lock_at": _dt(now + timedelta(days=37)), "archived_at": None,
            "shuffle_answers": rng.random() < 0.5, "title": f"Quiz {len(rows['quizzes'])+1}",
            "workflow_state": "active", "description": None,
            "time_limit": rng.choice([None, 20, 30, 60]), "access_code": None, "ip_filter": None,
            "one_question_at_a_time": False, "cant_go_back": False,
            "show_correct_answers": rng.random() < 0.7, "hide_results": False, "practice_quiz": False,
            "context_id": cid, "context_type": "Course", "migration_id": None,
            "quiz_type": "assignment", "points_possible": rng.choice([10, 25, 50, 100]),
            "assignment_group_id": None, "could_be_locked": False, "only_visible_to_overrides": False,
            "allowed_attempts": 1, "scoring_policy": "keep_highest",
            "anonymous_submissions": False, "assignment_id": aid,
        })
        reg.register("new_quizzes.quizzes", qid)

        # Quiz questions
        q_count = rng.randint(3, 10)
        for qn in range(1, q_count + 1):
            rows["quiz_questions"].append({
                "id": ids.next("new_quizzes_quiz_questions"),
                "created_at": created, "updated_at": created, "archived_at": None,
                "workflow_state": "active", "quiz_id": qid, "migration_id": None,
                "position": qn, "question_data": json.dumps({"points_possible": round(aid / q_count, 1)}),
                "item_id": None,
            })

        # Quiz submissions
        canvas_users = reg.ids("canvas.users")
        for uid in canvas_users[:min(len(canvas_users), max(3, cfg.students_per_course))]:
            if rng.random() > 0.1:
                qsid = ids.next("new_quizzes_quiz_submissions")
                started = now - timedelta(days=rng.randint(1, 20))
                finished = started + timedelta(seconds=rng.randint(300, 3600))
                score = rng.uniform(0, 100)
                rows["quiz_submissions"].append({
                    "id": qsid, "user_id": uid, "created_at": _dt(started),
                    "updated_at": _dt(finished), "workflow_state": "complete", "quiz_id": qid,
                    "started_at": _dt(started), "finished_at": _dt(finished), "end_at": _dt(finished),
                    "score": round(score, 1), "attempt": 1, "submission_data": None,
                    "fudge_points": 0.0, "quiz_points_possible": aid,
                    "extra_attempts": None, "extra_time": None,
                    "manually_scored": False, "was_preview": False, "has_seen_results": True,
                })
                reg.register("new_quizzes.quiz_submissions", qsid)

        # Assignment overrides
        if rng.random() < 0.3:
            ao_id = ids.next("new_quizzes_assignment_overrides")
            rows["assignment_overrides"].append({
                "id": ao_id, "all_day": False, "all_day_date": None,
                "assignment_id": aid, "assignment_version": None, "created_at": created,
                "due_at": _dt(now + timedelta(days=35)), "due_at_overridden": True,
                "lock_at": None, "lock_at_overridden": False,
                "quiz_id": None, "quiz_version": None, "set_id": None, "set_type": "ADHOC",
                "title": "Extended Deadline", "unlock_at": None, "unlock_at_overridden": False,
                "updated_at": created, "workflow_state": "active",
            })
            reg.register("new_quizzes.assignment_overrides", ao_id)

            # Override students
            if canvas_users:
                rows["assignment_override_students"].append({
                    "id": ids.next("new_quizzes_assignment_override_students"),
                    "user_id": rng.choice(canvas_users), "created_at": created,
                    "updated_at": created, "workflow_state": "active",
                    "assignment_id": aid, "assignment_override_id": ao_id,
                })

    return rows
