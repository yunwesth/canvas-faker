"""Generator for the canvas namespace (84 tables)."""
from __future__ import annotations

import json
import random
import string
from datetime import datetime, timedelta, timezone

from faker import Faker

from ..config import GenerationConfig
from ..ids import IdAllocator, Registry, new_uuid
from ..messiness import MessinessEngine
from ..providers import CanvasProvider, DEPARTMENTS

UTC = timezone.utc


def _dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _rand_dt(fake: Faker, start: datetime, end: datetime) -> str:
    return _dt(fake.date_time_between(start_date=start, end_date=end, tzinfo=UTC))


def generate(
    cfg: GenerationConfig,
    fake: Faker,
    ids: IdAllocator,
    reg: Registry,
    mess: MessinessEngine,
) -> dict[str, list[dict]]:
    """Return {table_name: [row_dict, ...]} for the canvas namespace."""
    rng = mess.rng
    now = datetime(2025, 8, 1, tzinfo=UTC)
    term_start_base = datetime(2024, 1, 1, tzinfo=UTC)

    rows: dict[str, list[dict]] = {t: [] for t in [
        "accounts", "roles", "enrollment_terms", "courses", "course_sections",
        "users", "pseudonyms", "communication_channels", "enrollments",
        "enrollment_states", "enrollment_dates_overrides",
        "assignment_groups", "assignments", "assignment_overrides",
        "assignment_override_students", "submissions", "submission_comments",
        "scores", "quizzes", "quiz_questions", "quiz_submissions",
        "discussion_topics", "discussion_entries", "discussion_entry_participants",
        "discussion_topic_participants", "context_modules", "context_module_progressions",
        "account_users", "user_account_associations", "course_account_associations",
        "favorites", "folders", "content_tags", "context_external_tools",
        "wiki_pages", "attachments", "attachment_associations", "calendar_events",
        "collaborations", "comment_bank_items", "content_migrations",
        "content_participation_counts", "content_participations", "content_shares",
        "conversations", "conversation_messages", "conversation_participants",
        "conversation_message_participants", "custom_gradebook_columns",
        "custom_gradebook_column_data", "developer_keys", "developer_key_account_bindings",
        "grading_period_groups", "grading_periods", "grading_standards",
        "group_categories", "groups", "group_memberships", "late_policies",
        "learning_outcomes", "learning_outcome_groups", "learning_outcome_results",
        "learning_outcome_question_results", "content_tags",
        "lti_line_items", "lti_resource_links", "lti_results",
        "media_objects", "post_policies", "rubrics", "rubric_associations",
        "rubric_assessments", "sis_batches", "scores", "usage_rights",
        "user_notes", "user_observation_links", "access_tokens",
        "assessment_question_banks", "assessment_questions",
        "canvadocs_annotation_contexts", "custom_grade_statuses",
        "role_overrides", "accessibility_issues", "accessibility_resource_scans",
        "originality_reports",
    ]}
    # deduplicate key list
    rows = {k: [] for k in dict.fromkeys(rows)}

    # ------------------------------------------------------------------
    # Accounts
    # ------------------------------------------------------------------
    root_account_id = ids.next("accounts")
    root_created = _dt(term_start_base - timedelta(days=365))
    rows["accounts"].append({
        "id": root_account_id, "created_at": root_created, "updated_at": root_created,
        "workflow_state": "active", "name": fake.company() + " University",
        "parent_account_id": None, "root_account_id": root_account_id,
        "sis_source_id": mess.sis_source_id(fake.sis_id("ACCT")),
        "sis_batch_id": None, "integration_id": None,
        "lti_guid": new_uuid(), "uuid": new_uuid(),
        "default_storage_quota": 5368709120, "default_user_storage_quota": 524288000,
        "default_group_storage_quota": 524288000, "default_time_zone": fake.timezone(),
    })
    reg.register("canvas.accounts", root_account_id)

    sub_account_ids = []
    for _ in range(cfg.n_sub_accounts):
        aid = ids.next("accounts")
        created = _dt(term_start_base - timedelta(days=rng.randint(100, 300)))
        rows["accounts"].append({
            "id": aid, "created_at": created, "updated_at": created,
            "workflow_state": "active", "name": fake.account_name(),
            "parent_account_id": root_account_id, "root_account_id": root_account_id,
            "sis_source_id": mess.sis_source_id(fake.sis_id("DEPT")),
            "sis_batch_id": None, "integration_id": None,
            "lti_guid": new_uuid(), "uuid": new_uuid(),
            "default_storage_quota": 1073741824, "default_user_storage_quota": 524288000,
            "default_group_storage_quota": 209715200, "default_time_zone": fake.timezone(),
        })
        sub_account_ids.append(aid)
        reg.register("canvas.accounts", aid)

    def pick_account():
        return rng.choice([root_account_id] + sub_account_ids)

    def _course_code():
        return fake.course_code()

    def _course_name(dept=None):
        return fake.course_name(dept)

    def _sis_id(prefix=None):
        return fake.sis_id(prefix)

    def _canvas_uuid():
        return fake.canvas_uuid()

    def _letter_grade(score_pct=None):
        return fake.letter_grade(score_pct)

    def _assignment_title(n=1):
        return fake.assignment_title(n)

    def _quiz_title(n=1):
        return fake.quiz_title(n)

    def _discussion_title(n=1):
        return fake.discussion_title(n)

    def _module_name(n=1):
        return fake.module_name(n)

    def _grader_comment():
        return fake.grader_comment()

    def _sortable_name(full_name):
        return fake.sortable_name(full_name)

    def _realistic_score(max_pts, mess_intensity=0.3):
        return fake.realistic_score(max_pts, mess_intensity)

    # ------------------------------------------------------------------
    # Roles
    # ------------------------------------------------------------------
    base_roles = [
        ("StudentEnrollment", "Student"), ("TeacherEnrollment", "Teacher"),
        ("TaEnrollment", "TA"), ("DesignerEnrollment", "Designer"),
        ("ObserverEnrollment", "Observer"),
    ]
    role_ids: dict[str, int] = {}
    for base_role_type, name in base_roles:
        rid = ids.next("roles")
        role_ids[base_role_type] = rid
        created = _dt(term_start_base - timedelta(days=400))
        rows["roles"].append({
            "id": rid, "created_at": created, "updated_at": created,
            "workflow_state": "active", "name": name, "label": name,
            "base_role_type": base_role_type, "account_id": root_account_id,
            "root_account_id": root_account_id,
        })
        reg.register("canvas.roles", rid)

    # ------------------------------------------------------------------
    # Enrollment terms
    # ------------------------------------------------------------------
    term_ids = []
    term_date_ranges = []
    for i in range(cfg.n_terms):
        tid = ids.next("enrollment_terms")
        year = 2024 + i // 2
        sem = "Spring" if i % 2 == 0 else "Fall"
        start = datetime(year, 1 if sem == "Spring" else 8, 15, tzinfo=UTC)
        end = datetime(year, 5 if sem == "Spring" else 12, 15, tzinfo=UTC)
        created = _dt(start - timedelta(days=60))
        rows["enrollment_terms"].append({
            "id": tid, "created_at": created, "updated_at": created,
            "workflow_state": "active", "root_account_id": root_account_id,
            "name": f"{sem} {year}", "sis_source_id": mess.sis_source_id(f"TERM-{sem[:2]}{year}"),
            "sis_batch_id": None, "integration_id": None,
            "start_at": _dt(start), "end_at": _dt(end), "grading_period_group_id": None,
        })
        term_ids.append(tid)
        term_date_ranges.append((start, end))
        reg.register("canvas.enrollment_terms", tid)

    # ------------------------------------------------------------------
    # Courses
    # ------------------------------------------------------------------
    course_ids = []
    course_term_map: dict[int, tuple[datetime, datetime]] = {}
    course_account_map: dict[int, int] = {}
    for i in range(cfg.n_courses):
        cid = ids.next("courses")
        dept = rng.choice(DEPARTMENTS)
        term_idx = rng.randint(0, len(term_ids) - 1)
        tid = term_ids[term_idx]
        start, end = term_date_ranges[term_idx]
        acct = pick_account()
        created = _dt(start - timedelta(days=rng.randint(30, 90)))
        ws = mess.workflow_state("available") if rng.random() > 0.08 else rng.choice(["completed", "available"])
        rows["courses"].append({
            "id": cid, "created_at": created, "updated_at": created,
            "workflow_state": ws, "name": fake.course_name(dept),
            "account_id": acct, "root_account_id": root_account_id,
            "enrollment_term_id": tid,
            "sis_source_id": mess.sis_source_id(fake.sis_id("COURSE")),
            "sis_batch_id": None, "integration_id": None,
            "course_code": fake.course_code(dept),
            "default_view": rng.choice(["modules", "syllabus", "wiki", "assignments"]),
            "license": rng.choice(["private", "public_domain", None]),
            "start_at": _dt(start), "conclude_at": _dt(end),
            "grading_standard_id": None, "is_public": rng.random() < 0.2,
            "allow_student_wiki_edits": False, "is_public_to_auth_users": False,
            "public_syllabus": rng.random() < 0.5, "public_syllabus_to_auth": False,
            "allow_student_forum_attachments": True, "open_enrollment": False,
            "self_enrollment": False, "restrict_enrollments_to_course_dates": False,
            "locale": mess.maybe_null(rng.choice(["en", "es", "fr", None])),
            "time_zone": fake.timezone(),
            "lti_context_id": new_uuid(), "storage_quota": 1073741824,
            "uuid": new_uuid(),
            "show_announcements_on_home_page": rng.random() < 0.5,
            "home_page_announcement_limit": rng.randint(3, 10),
            "homeroom_course": False, "template": False,
        })
        course_ids.append(cid)
        course_term_map[cid] = (start, end)
        course_account_map[cid] = acct
        reg.register("canvas.courses", cid)

    # ------------------------------------------------------------------
    # Course sections
    # ------------------------------------------------------------------
    section_ids_by_course: dict[int, list[int]] = {}
    for cid in course_ids:
        start, end = course_term_map[cid]
        sids = []
        for s in range(cfg.sections_per_course):
            sid = ids.next("course_sections")
            created = _dt(start - timedelta(days=rng.randint(10, 30)))
            rows["course_sections"].append({
                "id": sid, "created_at": created, "updated_at": created,
                "workflow_state": "active",
                "name": f"Section {string.ascii_uppercase[s]}",
                "course_id": cid, "root_account_id": root_account_id,
                "enrollment_term_id": rng.choice(term_ids),
                "sis_source_id": mess.sis_source_id(f"SEC-{cid}-{s+1}"),
                "sis_batch_id": None, "integration_id": None,
                "start_at": _dt(start), "end_at": _dt(end),
                "restrict_enrollments_to_section_dates": False,
                "nonxlist_course_id": None, "stuck_sis_fields": None,
            })
            sids.append(sid)
            reg.register("canvas.course_sections", sid)
        section_ids_by_course[cid] = sids

    # ------------------------------------------------------------------
    # Users (students + teachers)
    # ------------------------------------------------------------------
    all_user_ids: list[int] = []
    student_ids_by_course: dict[int, list[int]] = {}
    teacher_ids_by_course: dict[int, list[int]] = {}
    user_created_at: dict[int, str] = {}

    # Global student pool (students can be in multiple courses)
    n_students = max(cfg.n_courses * cfg.students_per_course // 3, 50)
    student_pool: list[int] = []
    for _ in range(n_students):
        uid = ids.next("users")
        full_name = fake.name()
        full_name = mess.name_with_typo(full_name)
        created = _rand_dt(fake, term_start_base - timedelta(days=500), term_start_base)
        rows["users"].append({
            "id": uid, "created_at": created, "updated_at": created,
            "workflow_state": mess.workflow_state("registered"),
            "name": full_name, "sortable_name": fake.sortable_name(full_name),
            "short_name": full_name.split()[0],
            "avatar_image_url": mess.maybe_null(fake.image_url()),
            "avatar_image_source": mess.maybe_null("attachment"),
            "avatar_image_updated_at": mess.maybe_null(created),
            "avatar_state": "none", "locale": mess.maybe_null(rng.choice(["en", "es", "fr"])),
            "time_zone": fake.timezone(), "uuid": fake.canvas_uuid(),
            "school_name": mess.maybe_null(fake.company()),
            "school_position": mess.maybe_null(rng.randint(0, 5)),
            "storage_quota": 524288000,
            "merged_into_user_id": None,  # filled later
            "lti_context_id": new_uuid(),
        })
        student_pool.append(uid)
        all_user_ids.append(uid)
        user_created_at[uid] = created
        reg.register("canvas.users", uid)

    # Apply user merges
    for uid in student_pool:
        merged = mess.merged_user_id(student_pool)
        if merged and merged != uid:
            rows["users"][-1]["merged_into_user_id"] = merged

    # Teacher pool
    teacher_pool: list[int] = []
    n_teachers = max(cfg.n_courses * cfg.teachers_per_course // 2, 10)
    for _ in range(n_teachers):
        uid = ids.next("users")
        full_name = fake.name()
        created = _rand_dt(fake, term_start_base - timedelta(days=600), term_start_base)
        rows["users"].append({
            "id": uid, "created_at": created, "updated_at": created,
            "workflow_state": "registered", "name": full_name,
            "sortable_name": fake.sortable_name(full_name),
            "short_name": full_name.split()[0],
            "avatar_image_url": mess.maybe_null(fake.image_url()),
            "avatar_image_source": mess.maybe_null("attachment"),
            "avatar_image_updated_at": mess.maybe_null(created),
            "avatar_state": mess.maybe_null("approved"),
            "locale": mess.maybe_null("en"), "time_zone": fake.timezone(),
            "uuid": fake.canvas_uuid(), "school_name": None,
            "school_position": None, "storage_quota": 524288000,
            "merged_into_user_id": None, "lti_context_id": new_uuid(),
        })
        teacher_pool.append(uid)
        all_user_ids.append(uid)
        user_created_at[uid] = created
        reg.register("canvas.users", uid)

    # ------------------------------------------------------------------
    # Pseudonyms & communication_channels
    # ------------------------------------------------------------------
    for uid in all_user_ids:
        pid = ids.next("pseudonyms")
        sis_uid = mess.sis_user_id(fake.sis_id("STU"))
        login = fake.user_name() + str(rng.randint(1, 99))
        rows["pseudonyms"].append({
            "id": pid, "created_at": user_created_at[uid],
            "updated_at": user_created_at[uid],
            "workflow_state": "active", "user_id": uid, "account_id": root_account_id,
            "unique_id": login, "sis_user_id": sis_uid, "integration_id": None,
            "sis_batch_id": None, "authentication_provider_id": None,
            "declared_user_type": mess.maybe_null(rng.choice(["student", "faculty", None])),
        })
        reg.register("canvas.pseudonyms", pid)

        cid = ids.next("communication_channels")
        email = fake.email()
        state = mess.comm_channel_state()
        bounce = mess.bounce_fields()
        rows["communication_channels"].append({
            "id": cid, "created_at": user_created_at[uid],
            "updated_at": user_created_at[uid],
            "workflow_state": state, "user_id": uid, "path_type": "email",
            "path": email, "position": 1,
            "bounce_count": bounce["bounce_count"],
            "last_bounce_at": bounce["last_bounce_at"],
        })
        reg.register("canvas.communication_channels", cid)

    # ------------------------------------------------------------------
    # Enrollments
    # ------------------------------------------------------------------
    enrollment_ids_by_course_user: dict[tuple[int, int], int] = {}
    all_student_enrollment_ids: list[int] = []

    for cid in course_ids:
        start, end = course_term_map[cid]
        acct = course_account_map[cid]
        sids = section_ids_by_course[cid]

        # Teachers
        teachers = rng.sample(teacher_pool, min(cfg.teachers_per_course, len(teacher_pool)))
        teacher_ids_by_course[cid] = teachers
        for tuid in teachers:
            eid = ids.next("enrollments")
            created = user_created_at.get(tuid, _dt(start))
            rows["enrollments"].append({
                "id": eid, "created_at": created, "updated_at": created,
                "workflow_state": "active", "user_id": tuid, "course_id": cid,
                "type": "TeacherEnrollment", "course_section_id": sids[0],
                "root_account_id": acct, "associated_user_id": None,
                "role_id": role_ids["TeacherEnrollment"],
                "sis_source_id": mess.sis_source_id(fake.sis_id("ENR")),
                "sis_batch_id": None, "integration_id": None,
                "start_at": _dt(start), "end_at": _dt(end), "completed_at": None,
                "last_activity_at": _rand_dt(fake, start, min(end, now)),
                "total_activity_time": rng.randint(3600, 360000),
                "grade_publishing_status": "unpublished", "last_publish_attempt_at": None,
                "self_enrolled": False, "self_reported_grade": None,
                "limit_privileges_to_course_section": False, "peer_reviews_count": 0,
                "grades_submitted_at": None,
            })
            reg.register("canvas.enrollments", eid)
            rows["enrollment_states"].append({
                "enrollment_id": eid, "state": "active", "state_is_current": True,
                "state_started_at": created, "state_valid_until": None,
                "restricted_access": False, "access_is_current": True,
            })

        # Students
        students = rng.sample(student_pool, min(cfg.students_per_course, len(student_pool)))
        student_ids_by_course[cid] = students
        for suid in students:
            eid = ids.next("enrollments")
            created = user_created_at.get(suid, _dt(start))
            ws = mess.enrollment_workflow_state()
            completed_at = _rand_dt(fake, start + timedelta(days=90), end) if ws == "completed" else None
            last_act = _rand_dt(fake, start, min(end, now)) if ws == "active" else None
            rows["enrollments"].append({
                "id": eid, "created_at": created, "updated_at": created,
                "workflow_state": ws, "user_id": suid, "course_id": cid,
                "type": "StudentEnrollment", "course_section_id": rng.choice(sids),
                "root_account_id": acct, "associated_user_id": None,
                "role_id": role_ids["StudentEnrollment"],
                "sis_source_id": mess.sis_source_id(fake.sis_id("ENR")),
                "sis_batch_id": None, "integration_id": None,
                "start_at": _dt(start), "end_at": _dt(end), "completed_at": completed_at,
                "last_activity_at": last_act,
                "total_activity_time": rng.randint(0, 200000) if ws == "active" else None,
                "grade_publishing_status": rng.choice(["unpublished", "published"]),
                "last_publish_attempt_at": None,
                "self_enrolled": mess.maybe_null(rng.random() < 0.05),
                "self_reported_grade": None,
                "limit_privileges_to_course_section": False, "peer_reviews_count": None,
                "grades_submitted_at": None,
            })
            enrollment_ids_by_course_user[(cid, suid)] = eid
            all_student_enrollment_ids.append(eid)
            reg.register("canvas.enrollments", eid)
            rows["enrollment_states"].append({
                "enrollment_id": eid, "state": ws, "state_is_current": True,
                "state_started_at": created, "state_valid_until": None,
                "restricted_access": ws != "active", "access_is_current": True,
            })

    # ------------------------------------------------------------------
    # Assignment groups + Assignments
    # ------------------------------------------------------------------
    assignment_ids_by_course: dict[int, list[int]] = {}
    assignment_pts: dict[int, float] = {}
    assignment_due: dict[int, str | None] = {}

    for cid in course_ids:
        start, end = course_term_map[cid]
        # One assignment group per course
        agid = ids.next("assignment_groups")
        created = _dt(start - timedelta(days=10))
        rows["assignment_groups"].append({
            "id": agid, "created_at": created, "updated_at": created,
            "workflow_state": "available", "name": "Assignments",
            "context_id": cid, "context_type": "Course", "group_weight": 100.0,
            "rules": None, "sis_source_id": None, "integration_data": None, "position": 1,
        })
        reg.register("canvas.assignment_groups", agid)

        aids = []
        for n in range(1, cfg.assignments_per_course + 1):
            aid = ids.next("assignments")
            pts = rng.choice([10.0, 20.0, 25.0, 50.0, 100.0])
            due = start + timedelta(days=rng.randint(7, int((end - start).days - 7)))
            due_str = _dt(due)
            unlock = _dt(due - timedelta(days=7))
            lock = _dt(due + timedelta(days=3))
            created = _dt(start - timedelta(days=5))
            rows["assignments"].append({
                "id": aid, "created_at": created, "updated_at": created,
                "workflow_state": "published", "title": fake.assignment_title(n),
                "description": mess.maybe_null(fake.sentence(nb_words=12)),
                "context_id": cid, "context_type": "Course",
                "assignment_group_id": agid, "grading_type": "points",
                "points_possible": pts, "due_at": due_str,
                "unlock_at": unlock, "lock_at": lock,
                "submission_types": [rng.choice(["online_upload", "online_text_entry"])],
                "grading_standard_id": None, "allowed_extensions": None,
                "peer_reviews": False, "automatic_peer_reviews": False,
                "peer_review_count": None, "peer_reviews_due_at": None,
                "peer_reviews_assigned": False, "moderated_grading": False,
                "grades_published_at": _dt(due + timedelta(days=7)),
                "grader_count": None, "anonymous_grading": False,
                "omit_from_final_grade": False, "position": n,
                "migration_id": None, "only_visible_to_overrides": False,
                "post_to_sis": True, "sis_source_id": None, "integration_id": None,
                "allowed_attempts": mess.maybe_null(rng.choice([None, 1, 3])),
                "has_sub_assignments": None, "important_dates": False,
                "duplicate_of_id": None, "lti_context_id": new_uuid(),
                "turnitin_enabled": rng.random() < 0.1, "vericite_enabled": False,
                "anonymous_instructor_annotations": False, "annotatable_attachment_id": None,
                "could_be_locked": False, "freeze_on_copy": False, "group_category_id": None,
                "grade_group_students_individually": False, "intra_group_peer_reviews": False,
                "final_grader_id": None, "grader_section_id": None,
                "grader_names_visible_to_final_grader": None,
                "graders_anonymous_to_graders": None,
                "grader_comments_visible_to_graders": None, "parent_assignment_id": None,
            })
            aids.append(aid)
            assignment_pts[aid] = pts
            assignment_due[aid] = due_str
            reg.register("canvas.assignments", aid)
        assignment_ids_by_course[cid] = aids

    # ------------------------------------------------------------------
    # Submissions
    # ------------------------------------------------------------------
    submission_ids_by_course_user: dict[tuple[int, int], list[int]] = {}

    for cid in course_ids:
        start, end = course_term_map[cid]
        students = student_ids_by_course.get(cid, [])
        teachers = teacher_ids_by_course.get(cid, [teacher_pool[0]] if teacher_pool else [])
        aids = assignment_ids_by_course.get(cid, [])

        for suid in students:
            eid = enrollment_ids_by_course_user.get((cid, suid))
            subs_for_pair = []
            for aid in aids:
                pts = assignment_pts[aid]
                due = assignment_due[aid]
                status = mess.submission_status(due)

                if status["missing"]:
                    raw_score = None
                    submitted_at = None
                else:
                    raw_score = fake.realistic_score(pts, cfg.messiness.intensity)
                    submitted_at = _rand_dt(fake, start, end)

                sg = mess.score_and_grade(raw_score, pts, fake)
                grader_id = rng.choice(teachers) if teachers else None
                graded_at = _rand_dt(fake, start, end) if raw_score is not None else None

                sub_id = ids.next("submissions")
                rows["submissions"].append({
                    "id": sub_id, "created_at": user_created_at.get(suid, submitted_at or _dt(start)),
                    "updated_at": graded_at or submitted_at or _dt(start),
                    "workflow_state": "graded" if raw_score is not None else "unsubmitted",
                    "user_id": suid, "assignment_id": aid, "course_id": cid,
                    "submitted_at": submitted_at, "graded_at": graded_at,
                    "grader_id": grader_id, "score": sg["score"], "grade": sg["grade"],
                    "published_score": sg["published_score"],
                    "published_grade": sg["published_grade"],
                    "submission_type": mess.maybe_null(rng.choice(["online_upload", "online_text_entry"])) if submitted_at else None,
                    "url": None, "body": None, "attempt": 1 if submitted_at else None,
                    "group_id": None, "attachment_ids": None,
                    "grade_matches_current_submission": True,
                    "grading_period_id": None,
                    "late": status["late"], "missing": status["missing"],
                    "late_policy_status": status["late_policy_status"],
                    "seconds_late": status["seconds_late"],
                    "excused": status["excused"],
                    "posted_at": graded_at, "redo_request": False,
                    "cached_due_date": due,
                    "resource_link_lookup_uuid": None, "anonymous_id": None,
                    "extra_attempts": None, "process_attempts": 0,
                })
                subs_for_pair.append(sub_id)
                reg.register("canvas.submissions", sub_id)

                # Submission comment (~40% of graded submissions)
                if raw_score is not None and rng.random() < 0.4:
                    scid = ids.next("submission_comments")
                    rows["submission_comments"].append({
                        "id": scid, "created_at": graded_at, "updated_at": graded_at,
                        "workflow_state": "active", "submission_id": sub_id,
                        "author_id": grader_id, "comment": fake.grader_comment(),
                        "attachment_ids": None, "media_comment_id": None,
                        "media_comment_type": None, "provisional_grade_id": None,
                        "anonymous": False, "hidden": False, "attempt": 1,
                        "group_comment_id": None, "draft": False,
                    })

            submission_ids_by_course_user[(cid, suid)] = subs_for_pair

    # ------------------------------------------------------------------
    # Scores (one per enrollment + course_score)
    # ------------------------------------------------------------------
    for cid in course_ids:
        students = student_ids_by_course.get(cid, [])
        aids = assignment_ids_by_course.get(cid, [])
        for suid in students:
            eid = enrollment_ids_by_course_user.get((cid, suid))
            if not eid:
                continue
            # Compute a synthetic overall score
            raw_scores = []
            for aid in aids:
                pts = assignment_pts[aid]
                rs = fake.realistic_score(pts, cfg.messiness.intensity)
                if rng.random() > 0.15:  # 15% missing
                    raw_scores.append((rs, pts))

            if raw_scores:
                total = sum(s for s, _ in raw_scores)
                possible = sum(p for _, p in raw_scores)
                pct = total / possible * 100 if possible else 0.0
            else:
                pct = 0.0

            sg = mess.score_and_grade(pct, 100.0, fake)
            created = _dt(now - timedelta(days=rng.randint(1, 30)))
            rows["scores"].append({
                "id": ids.next("scores"), "created_at": created, "updated_at": created,
                "workflow_state": "active", "enrollment_id": eid,
                "course_score": True, "grading_period_id": None,
                "current_score": sg["current_score"],
                "final_score": sg["final_score"],
                "unposted_current_score": sg["unposted_current_score"],
                "unposted_final_score": sg["unposted_final_score"],
                "override_score": sg["override_score"],
                "current_grade": sg["current_grade"],
                "final_grade": sg["final_grade"],
                "unposted_current_grade": sg["unposted_current_grade"],
                "unposted_final_grade": sg["unposted_final_grade"],
                "override_grade": sg["override_grade"],
            })
            reg.register("canvas.scores", ids.peek("scores"))

    # ------------------------------------------------------------------
    # Quizzes + quiz_questions + quiz_submissions
    # ------------------------------------------------------------------
    quiz_ids_by_course: dict[int, list[int]] = {}

    for cid in course_ids:
        start, end = course_term_map[cid]
        agid = None
        for row in rows["assignment_groups"]:
            if row["context_id"] == cid:
                agid = row["id"]
                break

        qids = []
        for n in range(1, cfg.quizzes_per_course + 1):
            aid = ids.next("assignments")
            pts = rng.choice([10.0, 20.0, 50.0])
            due = start + timedelta(days=rng.randint(7, int((end - start).days - 7)))
            quiz_id = ids.next("quizzes")
            created = _dt(start - timedelta(days=5))
            due_str = _dt(due)

            rows["assignments"].append({
                "id": aid, "created_at": created, "updated_at": created,
                "workflow_state": "published",
                "title": fake.quiz_title(n),
                "description": None, "context_id": cid, "context_type": "Course",
                "assignment_group_id": agid, "grading_type": "points",
                "points_possible": pts, "due_at": due_str,
                "unlock_at": _dt(due - timedelta(days=7)), "lock_at": _dt(due + timedelta(days=1)),
                "submission_types": ["online_quiz"], "grading_standard_id": None,
                "allowed_extensions": None, "peer_reviews": False, "automatic_peer_reviews": False,
                "peer_review_count": None, "peer_reviews_due_at": None, "peer_reviews_assigned": False,
                "moderated_grading": False, "grades_published_at": _dt(due + timedelta(days=2)),
                "grader_count": None, "anonymous_grading": None, "omit_from_final_grade": False,
                "position": cfg.assignments_per_course + n, "migration_id": None,
                "only_visible_to_overrides": False, "post_to_sis": True,
                "sis_source_id": None, "integration_id": None, "allowed_attempts": 1,
                "has_sub_assignments": None, "important_dates": False, "duplicate_of_id": None,
                "lti_context_id": new_uuid(), "turnitin_enabled": False, "vericite_enabled": False,
                "anonymous_instructor_annotations": False, "annotatable_attachment_id": None,
                "could_be_locked": False, "freeze_on_copy": False, "group_category_id": None,
                "grade_group_students_individually": False, "intra_group_peer_reviews": False,
                "final_grader_id": None, "grader_section_id": None,
                "grader_names_visible_to_final_grader": None, "graders_anonymous_to_graders": None,
                "grader_comments_visible_to_graders": None, "parent_assignment_id": None,
            })
            reg.register("canvas.assignments", aid)
            assignment_pts[aid] = pts
            assignment_due[aid] = due_str

            q_count = rng.randint(5, 15)
            rows["quizzes"].append({
                "id": quiz_id, "created_at": created, "updated_at": created,
                "workflow_state": "available",
                "title": fake.quiz_title(n), "description": None,
                "due_at": due_str, "unlock_at": _dt(due - timedelta(days=7)),
                "lock_at": _dt(due + timedelta(days=1)),
                "points_possible": pts, "assignment_id": aid,
                "context_id": cid, "quiz_type": "assignment",
                "assignment_group_id": agid, "shuffle_answers": rng.random() < 0.5,
                "show_correct_answers": rng.random() < 0.7,
                "time_limit": rng.choice([None, 20, 30, 60]),
                "allowed_attempts": 1, "scoring_policy": "keep_highest",
                "access_code": None, "ip_filter": None, "anonymous_submissions": False,
                "only_visible_to_overrides": False, "one_question_at_a_time": False,
                "cant_go_back": False, "has_access_code": False,
                "question_count": q_count, "unpublished_question_count": 0,
                "could_be_locked": False, "migration_id": None,
            })
            reg.register("canvas.quizzes", quiz_id)
            qids.append(quiz_id)

            # Quiz questions
            for qn in range(1, q_count + 1):
                qqid = ids.next("quiz_questions")
                rows["quiz_questions"].append({
                    "id": qqid, "created_at": created, "updated_at": created,
                    "workflow_state": "published", "quiz_id": quiz_id,
                    "assessment_question_id": None, "assessment_question_version": None,
                    "position": qn, "question_data": json.dumps({"question_type": "multiple_choice_question", "question_name": f"Q{qn}", "points_possible": round(pts / q_count, 1)}),
                    "quiz_group_id": None, "migration_id": None,
                })

            # Quiz submissions
            students = student_ids_by_course.get(cid, [])
            for suid in students:
                if rng.random() < 0.1:  # 10% didn't take it
                    continue
                raw = fake.realistic_score(pts, cfg.messiness.intensity)
                time_spent = rng.randint(300, int((due - start).total_seconds()))
                started = fake.date_time_between(start_date=start, end_date=due, tzinfo=UTC)
                finished = started + timedelta(seconds=time_spent)
                sub_id = reg.ids("canvas.submissions")
                sub_ref = rng.choice(sub_id) if sub_id else None
                qsid = ids.next("quiz_submissions")
                rows["quiz_submissions"].append({
                    "id": qsid, "created_at": _dt(started), "updated_at": _dt(finished),
                    "workflow_state": "complete", "user_id": suid, "quiz_id": quiz_id,
                    "submission_id": sub_ref, "score": raw, "kept_score": raw,
                    "attempt": 1, "extra_attempts": None, "extra_time": None,
                    "manually_scored": False, "manually_unlocked": False,
                    "quiz_points_possible": pts, "score_before_regrade": None,
                    "fudge_points": 0.0, "has_seen_results": True, "was_preview": False,
                    "time_spent": time_spent, "end_at": _dt(finished),
                    "finished_at": _dt(finished), "started_at": _dt(started),
                })
                reg.register("canvas.quiz_submissions", qsid)

        quiz_ids_by_course[cid] = qids
        reg.register("canvas.quiz_ids_by_course", cid)  # not a real FK, just tracking

    # ------------------------------------------------------------------
    # Discussion topics + entries + participants
    # ------------------------------------------------------------------
    discussion_ids_by_course: dict[int, list[int]] = {}
    for cid in course_ids:
        start, end = course_term_map[cid]
        dids = []
        for n in range(1, cfg.discussions_per_course + 1):
            did = ids.next("discussion_topics")
            posted = _rand_dt(fake, start, end)
            rows["discussion_topics"].append({
                "id": did, "created_at": posted, "updated_at": posted,
                "workflow_state": "active",
                "title": fake.discussion_title(n),
                "message": fake.paragraph(nb_sentences=3),
                "context_id": cid, "context_type": "Course",
                "user_id": None, "assignment_id": None, "attachment_id": None,
                "discussion_type": "side_comment", "lock_at": None,
                "last_reply_at": posted, "posted_at": posted, "delayed_post_at": None,
                "could_be_locked": False, "position": n, "is_announcement": n == 1,
                "pinned": n == 1, "locked": False, "todo_date": None, "allow_rating": False,
                "only_graders_can_rate": False, "sort_by_rating": False, "podcast_enabled": False,
                "podcast_has_student_posts": False, "require_initial_post": True,
                "migration_id": None, "group_category_id": None, "anonymous_state": None,
            })
            dids.append(did)
            reg.register("canvas.discussion_topics", did)

            # Students post entries
            students = student_ids_by_course.get(cid, [])
            for suid in rng.sample(students, min(len(students), max(3, len(students) // 2))):
                entry_id = ids.next("discussion_entries")
                entry_created = _rand_dt(fake, start, end)
                rows["discussion_entries"].append({
                    "id": entry_id, "created_at": entry_created, "updated_at": entry_created,
                    "workflow_state": "active", "parent_id": None,
                    "discussion_topic_id": did, "user_id": suid, "editor_id": None,
                    "message": fake.paragraph(nb_sentences=2),
                    "rating_count": rng.randint(0, 5), "rating_sum": rng.randint(0, 5),
                    "depth": 1, "root_entry_id": None, "is_anonymous_author": False,
                })
                reg.register("canvas.discussion_entries", entry_id)
                rows["discussion_entry_participants"].append({
                    "id": ids.next("discussion_entry_participants"),
                    "created_at": entry_created, "updated_at": entry_created,
                    "discussion_entry_id": entry_id, "user_id": suid,
                    "workflow_state": "read", "rating": None,
                })

            # Topic participants
            for suid in students:
                rows["discussion_topic_participants"].append({
                    "id": ids.next("discussion_topic_participants"),
                    "created_at": posted, "updated_at": posted,
                    "discussion_topic_id": did, "user_id": suid,
                    "unread_entry_count": rng.randint(0, 5),
                    "workflow_state": "unread",
                    "subscribed": rng.random() < 0.7, "subscribed_timestamp": None,
                })
        discussion_ids_by_course[cid] = dids

    # ------------------------------------------------------------------
    # Context modules + progressions
    # ------------------------------------------------------------------
    module_ids_by_course: dict[int, list[int]] = {}
    for cid in course_ids:
        start, end = course_term_map[cid]
        mids = []
        for n in range(1, cfg.modules_per_course + 1):
            mid = ids.next("context_modules")
            unlock = start + timedelta(days=(n - 1) * 14)
            created = _dt(start - timedelta(days=5))
            rows["context_modules"].append({
                "id": mid, "created_at": created, "updated_at": created,
                "workflow_state": "active", "context_id": cid, "context_type": "Course",
                "name": fake.module_name(n), "position": n,
                "unlock_at": _dt(unlock), "completion_requirements": None,
                "prerequisites": None, "require_sequential_progress": False, "migration_id": None,
            })
            mids.append(mid)
            reg.register("canvas.context_modules", mid)

            # Progressions
            students = student_ids_by_course.get(cid, [])
            for suid in students:
                ws = rng.choice(["completed", "started", "unlocked", "locked"])
                completed_at = _rand_dt(fake, unlock, end) if ws == "completed" else None
                rows["context_module_progressions"].append({
                    "id": ids.next("context_module_progressions"),
                    "created_at": _dt(unlock), "updated_at": _dt(unlock),
                    "workflow_state": ws, "context_module_id": mid, "user_id": suid,
                    "requirements_met": None, "current_position": rng.randint(0, 5),
                    "completed_at": completed_at, "current": ws == "started",
                    "lock_version": 0, "evaluated_at": _dt(now - timedelta(days=1)),
                })
        module_ids_by_course[cid] = mids

    # ------------------------------------------------------------------
    # Peripheral canvas tables (schema-valid, lightly linked)
    # ------------------------------------------------------------------
    acct_list = reg.ids("canvas.accounts")
    user_list = reg.ids("canvas.users")
    course_list = reg.ids("canvas.courses")
    sub_list = reg.ids("canvas.submissions")
    assign_list = reg.ids("canvas.assignments")

    # account_users
    for uid in teacher_pool[:min(len(teacher_pool), 5)]:
        rows["account_users"].append({
            "id": ids.next("account_users"), "created_at": _dt(now - timedelta(days=200)),
            "updated_at": _dt(now - timedelta(days=200)), "workflow_state": "active",
            "account_id": root_account_id, "user_id": uid,
            "role_id": role_ids["TeacherEnrollment"], "sis_batch_id": None,
        })

    # user_account_associations
    for uid in user_list[:min(len(user_list), 20)]:
        rows["user_account_associations"].append({
            "id": ids.next("user_account_associations"),
            "created_at": _dt(now - timedelta(days=100)),
            "updated_at": _dt(now - timedelta(days=100)),
            "user_id": uid, "account_id": root_account_id, "depth": 0,
        })

    # course_account_associations
    for cid in course_list[:min(len(course_list), 20)]:
        rows["course_account_associations"].append({
            "id": ids.next("course_account_associations"),
            "created_at": _dt(now - timedelta(days=300)),
            "updated_at": _dt(now - timedelta(days=300)),
            "course_id": cid, "account_id": root_account_id,
            "course_section_id": None, "depth": 0,
        })

    # developer_keys
    dk_ids = []
    for _ in range(3):
        dkid = ids.next("developer_keys")
        rows["developer_keys"].append({
            "id": dkid, "created_at": _dt(now - timedelta(days=300)),
            "updated_at": _dt(now - timedelta(days=300)),
            "workflow_state": "active", "name": rng.choice(["Turnitin", "Kaltura", "Panopto"]),
            "user_id": None, "email": fake.company_email(), "redirect_uri": None, "api_key": None,
            "icon_url": None, "account_id": root_account_id, "visible": True, "is_lti_key": True,
            "public_jwk": None, "public_jwk_url": None, "scopes": None,
            "client_credentials_audience": None,
        })
        dk_ids.append(dkid)
        reg.register("canvas.developer_keys", dkid)

    # developer_key_account_bindings
    for dkid in dk_ids:
        rows["developer_key_account_bindings"].append({
            "id": ids.next("developer_key_account_bindings"),
            "created_at": _dt(now - timedelta(days=200)),
            "updated_at": _dt(now - timedelta(days=200)),
            "workflow_state": "on", "account_id": root_account_id, "developer_key_id": dkid,
        })

    # late_policies
    for cid in course_list[:min(len(course_list), 10)]:
        rows["late_policies"].append({
            "id": ids.next("late_policies"), "created_at": _dt(now - timedelta(days=60)),
            "updated_at": _dt(now - timedelta(days=60)), "course_id": cid,
            "missing_submission_deduction_enabled": True, "missing_submission_deduction": 100.0,
            "late_submission_deduction_enabled": True, "late_submission_deduction": 10.0,
            "late_submission_interval": "day", "late_submission_minimum_percent_enabled": False,
            "late_submission_minimum_percent": 0.0,
        })

    # post_policies
    for cid in course_list[:min(len(course_list), 10)]:
        rows["post_policies"].append({
            "id": ids.next("post_policies"), "created_at": _dt(now - timedelta(days=60)),
            "updated_at": _dt(now - timedelta(days=60)), "workflow_state": "active",
            "post_manually": rng.random() < 0.3, "course_id": cid, "assignment_id": None,
        })

    # favorites
    for uid in user_list[:min(len(user_list), 20)]:
        if course_list:
            rows["favorites"].append({
                "id": ids.next("favorites"), "created_at": _dt(now - timedelta(days=30)),
                "updated_at": _dt(now - timedelta(days=30)),
                "user_id": uid, "context_id": rng.choice(course_list), "context_type": "Course",
            })

    # folders
    for cid in course_list[:min(len(course_list), 5)]:
        rows["folders"].append({
            "id": ids.next("folders"), "created_at": _dt(now - timedelta(days=90)),
            "updated_at": _dt(now - timedelta(days=90)), "workflow_state": "visible",
            "name": "course files", "full_name": "course files", "context_id": cid,
            "context_type": "Course", "parent_folder_id": None, "position": 1,
            "lock_at": None, "locked": False, "hidden": False, "unlock_at": None,
            "submission_context_code": None, "unique_type": None,
        })
        reg.register("canvas.folders", ids.peek("folders"))

    # attachments
    folder_ids = reg.ids("canvas.folders")
    att_ids = []
    for _ in range(min(10, len(folder_ids) * 3)):
        attid = ids.next("attachments")
        fname = fake.file_name(extension=rng.choice(["pdf", "docx", "jpg", "png"]))
        rows["attachments"].append({
            "id": attid, "created_at": _dt(now - timedelta(days=50)),
            "updated_at": _dt(now - timedelta(days=50)), "workflow_state": "processed",
            "context_id": rng.choice(course_list) if course_list else 1,
            "context_type": "Course",
            "folder_id": rng.choice(folder_ids) if folder_ids else None,
            "user_id": rng.choice(user_list) if user_list else None,
            "filename": fname, "content_type": "application/pdf", "size": rng.randint(1024, 5000000),
            "display_name": fname, "file_state": "available", "media_entry_id": None,
            "could_be_locked": False, "locked": False, "locked_for_user": False, "category": None,
            "usage_rights_id": None, "visibility_level": "course", "migration_id": None,
        })
        att_ids.append(attid)
        reg.register("canvas.attachments", attid)

    # attachment_associations
    for attid in att_ids[:5]:
        rows["attachment_associations"].append({
            "id": ids.next("attachment_associations"), "created_at": _dt(now - timedelta(days=40)),
            "updated_at": _dt(now - timedelta(days=40)), "attachment_id": attid,
            "context_id": rng.choice(course_list) if course_list else 1, "context_type": "Course",
        })

    # wiki_pages
    for cid in course_list[:min(len(course_list), 5)]:
        rows["wiki_pages"].append({
            "id": ids.next("wiki_pages"), "created_at": _dt(now - timedelta(days=60)),
            "updated_at": _dt(now - timedelta(days=60)), "workflow_state": "active",
            "title": "Syllabus", "body": fake.paragraph(nb_sentences=3*3),
            "user_id": rng.choice(teacher_pool) if teacher_pool else None,
            "url": "syllabus", "context_id": cid, "context_type": "Course", "wiki_id": cid,
            "editing_roles": "teachers", "could_be_locked": False, "todo_date": None,
            "published": True, "publish_at": None,
        })

    # calendar_events
    for cid in course_list[:min(len(course_list), 5)]:
        event_start = now + timedelta(days=rng.randint(1, 30))
        rows["calendar_events"].append({
            "id": ids.next("calendar_events"), "created_at": _dt(now - timedelta(days=10)),
            "updated_at": _dt(now - timedelta(days=10)), "workflow_state": "active",
            "title": f"Office Hours", "description": None,
            "start_at": _dt(event_start), "end_at": _dt(event_start + timedelta(hours=1)),
            "context_id": cid, "context_type": "Course",
            "user_id": rng.choice(teacher_pool) if teacher_pool else None,
            "all_day": False, "all_day_date": None, "location_name": "Room 101",
            "location_address": None, "child_event_data": None,
            "parent_calendar_event_id": None, "effective_context_code": None,
            "migration_id": None, "important_dates": False,
        })

    # grading_period_groups + grading_periods
    gpg_id = ids.next("grading_period_groups")
    rows["grading_period_groups"].append({
        "id": gpg_id, "created_at": _dt(now - timedelta(days=300)),
        "updated_at": _dt(now - timedelta(days=300)), "workflow_state": "active",
        "account_id": root_account_id, "course_id": None, "weighted": False,
        "display_totals_for_all_grading_periods": True, "title": "Default Grading Periods",
    })
    reg.register("canvas.grading_period_groups", gpg_id)
    for i, (start, end) in enumerate(term_date_ranges):
        gp_id = ids.next("grading_periods")
        rows["grading_periods"].append({
            "id": gp_id, "created_at": _dt(start), "updated_at": _dt(start),
            "workflow_state": "active", "grading_period_group_id": gpg_id,
            "title": f"Period {i+1}", "weight": None, "start_date": _dt(start),
            "end_date": _dt(end), "close_date": _dt(end + timedelta(days=7)),
        })
        reg.register("canvas.grading_periods", gp_id)

    # grading_standards
    gs_id = ids.next("grading_standards")
    rows["grading_standards"].append({
        "id": gs_id, "created_at": _dt(now - timedelta(days=365)),
        "updated_at": _dt(now - timedelta(days=365)), "workflow_state": "active",
        "title": "Default Grading Scale",
        "data": json.dumps([["A", 0.93], ["A-", 0.90], ["B+", 0.87], ["B", 0.83],
                             ["B-", 0.80], ["C+", 0.77], ["C", 0.73], ["C-", 0.70],
                             ["D+", 0.67], ["D", 0.60], ["F", 0.0]]),
        "context_id": root_account_id, "context_type": "Account",
        "context_code": f"account_{root_account_id}", "version": 1,
        "user_id": None, "root_account_id": root_account_id, "migration_id": None,
        "usage_count": len(course_list),
    })
    reg.register("canvas.grading_standards", gs_id)

    # comment_bank_items
    for cid in course_list[:min(len(course_list), 3)]:
        if teacher_pool:
            rows["comment_bank_items"].append({
                "id": ids.next("comment_bank_items"),
                "created_at": _dt(now - timedelta(days=30)),
                "updated_at": _dt(now - timedelta(days=30)), "workflow_state": "active",
                "course_id": cid, "user_id": rng.choice(teacher_pool),
                "comment": fake.grader_comment(),
            })

    # content_tags (module items)
    for cid in course_list[:min(len(course_list), 5)]:
        mids = module_ids_by_course.get(cid, [])
        aids = assignment_ids_by_course.get(cid, [])
        for mid in mids:
            if aids:
                rows["content_tags"].append({
                    "id": ids.next("content_tags"),
                    "created_at": _dt(now - timedelta(days=60)),
                    "updated_at": _dt(now - timedelta(days=60)),
                    "workflow_state": "active", "context_id": cid, "context_type": "Course",
                    "content_id": rng.choice(aids), "content_type": "Assignment",
                    "context_module_id": mid, "tag_type": "context_module_item",
                    "title": "Assignment Item", "url": None, "position": 1, "indent": 0,
                    "migration_id": None, "learning_outcome_id": None,
                    "rubric_association_id": None, "mastery_score": None,
                    "completion_requirement": None, "associated_asset_id": None,
                    "associated_asset_type": None, "new_tab": False, "external_url": None,
                })
                reg.register("canvas.content_tags", ids.peek("content_tags"))

    # context_external_tools
    for _ in range(1):
        name, domain = fake.lti_tool()
        cet_id = ids.next("context_external_tools")
        rows["context_external_tools"].append({
            "id": cet_id, "created_at": _dt(now - timedelta(days=200)),
            "updated_at": _dt(now - timedelta(days=200)), "workflow_state": "active",
            "context_id": root_account_id, "context_type": "Account",
            "name": name, "tool_id": domain, "domain": domain, "url": f"https://{domain}/launch",
            "consumer_key": fake.uuid4()[:20], "privacy_level": "public", "settings": None,
            "migration_id": None, "developer_key_id": dk_ids[0] if dk_ids else None,
            "root_account_id": root_account_id, "lti_version": "1.3",
        })
        reg.register("canvas.context_external_tools", cet_id)

    # learning_outcomes + groups + results
    lo_group_id = ids.next("learning_outcome_groups")
    rows["learning_outcome_groups"].append({
        "id": lo_group_id, "created_at": _dt(now - timedelta(days=300)),
        "updated_at": _dt(now - timedelta(days=300)), "workflow_state": "active",
        "context_id": root_account_id, "context_type": "Account",
        "title": "Core Outcomes", "description": None, "vendor_guid": None,
        "root_account_id": root_account_id, "root_learning_outcome_group_id": lo_group_id,
        "source_outcome_group_id": None, "learning_outcome_group_id": None, "migration_id": None,
    })
    reg.register("canvas.learning_outcome_groups", lo_group_id)

    lo_ids = []
    for n in range(3):
        lo_id = ids.next("learning_outcomes")
        rows["learning_outcomes"].append({
            "id": lo_id, "created_at": _dt(now - timedelta(days=300)),
            "updated_at": _dt(now - timedelta(days=300)), "workflow_state": "active",
            "context_id": root_account_id, "context_type": "Account",
            "short_description": f"Outcome {n+1}",
            "description": fake.sentence(), "data": None, "vendor_guid": None,
            "root_account_id": root_account_id, "title": f"Learning Outcome {n+1}",
            "migration_id": None,
        })
        lo_ids.append(lo_id)
        reg.register("canvas.learning_outcomes", lo_id)

    # learning_outcome_results (need content_tags)
    ct_ids = reg.ids("canvas.content_tags")
    if ct_ids and lo_ids and user_list:
        for lo_id in lo_ids[:2]:
            for uid in user_list[:min(5, len(user_list))]:
                score = rng.uniform(0, 4)
                rows["learning_outcome_results"].append({
                    "id": ids.next("learning_outcome_results"),
                    "created_at": _dt(now - timedelta(days=30)),
                    "updated_at": _dt(now - timedelta(days=30)),
                    "workflow_state": "active", "user_id": uid,
                    "content_tag_id": rng.choice(ct_ids),
                    "context_id": root_account_id, "context_type": "Account",
                    "learning_outcome_id": lo_id, "association_id": None,
                    "association_type": None, "artifact_id": None, "artifact_type": None,
                    "score": round(score, 2), "possible": 4.0,
                    "mastery": score >= 3.0, "percent": round(score / 4.0, 4),
                    "attempt": 1, "assessed_at": _dt(now - timedelta(days=30)),
                    "submitted_or_assessed_at": _dt(now - timedelta(days=30)),
                    "original_score": round(score, 2), "original_possible": 4.0,
                    "original_mastery": score >= 3.0, "alignment_id": None,
                    "hide_points": False, "hidden": False, "learning_outcome_group_id": lo_group_id,
                })

    # lti_line_items + lti_results
    cet_ids = reg.ids("canvas.context_external_tools")
    if cet_ids and assign_list:
        li_id = ids.next("lti_line_items")
        aid = rng.choice(assign_list)
        rows["lti_line_items"].append({
            "id": li_id, "created_at": _dt(now - timedelta(days=60)),
            "updated_at": _dt(now - timedelta(days=60)), "workflow_state": "active",
            "score_maximum": 100.0, "label": "Final Grade", "tag": None,
            "resource_id": None, "coupled": True,
            "context_id": rng.choice(course_list) if course_list else 1,
            "resource_link_id": None, "assignment_id": aid, "client_id": None,
            "lti_resource_link_id": None, "lookup_id": new_uuid(), "extensions": None,
        })
        reg.register("canvas.lti_line_items", li_id)
        if user_list and sub_list:
            rows["lti_results"].append({
                "id": ids.next("lti_results"), "created_at": _dt(now - timedelta(days=30)),
                "updated_at": _dt(now - timedelta(days=30)), "workflow_state": "active",
                "line_item_id": li_id, "user_id": rng.choice(user_list),
                "result_score": rng.uniform(0, 100), "result_maximum": 100.0,
                "activity_progress": "Completed", "grading_progress": "FullyGraded",
                "submission_id": rng.choice(sub_list), "extensions": None,
            })

    # lti_resource_links
    if cet_ids and course_list:
        rows["lti_resource_links"].append({
            "id": ids.next("lti_resource_links"), "created_at": _dt(now - timedelta(days=90)),
            "updated_at": _dt(now - timedelta(days=90)), "workflow_state": "active",
            "context_id": rng.choice(course_list), "context_type": "Course",
            "context_external_tool_id": rng.choice(cet_ids), "custom": None,
            "lookup_id": new_uuid(), "resource_link_uuid": new_uuid(),
        })

    # rubrics + associations + assessments
    if course_list and user_list and sub_list:
        rub_id = ids.next("rubrics")
        cid = rng.choice(course_list)
        rows["rubrics"].append({
            "id": rub_id, "created_at": _dt(now - timedelta(days=100)),
            "updated_at": _dt(now - timedelta(days=100)), "workflow_state": "active",
            "user_id": rng.choice(teacher_pool) if teacher_pool else None,
            "context_id": cid, "context_type": "Course",
            "data": json.dumps([{"description": "Quality", "points": 10, "ratings": [{"description": "Excellent", "points": 10}, {"description": "Needs Work", "points": 5}]}]),
            "points_possible": 10.0, "title": "Writing Rubric", "description": None,
            "reusable": True, "read_only": False, "free_form_criterion_comments": False,
            "hide_score_total": False, "will_overwrite_submissions": None, "migration_id": None,
        })
        reg.register("canvas.rubrics", rub_id)
        ra_id = ids.next("rubric_associations")
        rows["rubric_associations"].append({
            "id": ra_id, "created_at": _dt(now - timedelta(days=100)),
            "updated_at": _dt(now - timedelta(days=100)), "workflow_state": "active",
            "rubric_id": rub_id, "association_id": cid, "association_type": "Course",
            "context_id": cid, "context_type": "Course", "use_for_grading": True,
            "purpose": "grading", "summary_data": None, "hide_score_total": False,
            "bookmarked": False, "hide_points": False, "hide_outcome_results": False,
        })
        reg.register("canvas.rubric_associations", ra_id)
        grader = rng.choice(teacher_pool) if teacher_pool else rng.choice(user_list)
        rows["rubric_assessments"].append({
            "id": ids.next("rubric_assessments"),
            "created_at": _dt(now - timedelta(days=30)),
            "updated_at": _dt(now - timedelta(days=30)), "workflow_state": "active",
            "rubric_id": rub_id, "rubric_association_id": ra_id,
            "user_id": rng.choice(user_list), "assessor_id": grader,
            "artifact_id": rng.choice(sub_list), "artifact_type": "Submission",
            "data": json.dumps([{"criterion_id": "1", "points": rng.choice([5, 10])}]),
            "score": rng.choice([5.0, 10.0]), "assessment_type": "grading",
        })

    # sis_batches
    rows["sis_batches"].append({
        "id": ids.next("sis_batches"), "created_at": _dt(now - timedelta(days=30)),
        "updated_at": _dt(now - timedelta(days=30)), "workflow_state": "imported",
        "account_id": root_account_id, "ended_at": _dt(now - timedelta(days=30)),
        "data": None, "progress": 100, "errors_attachment_id": None, "user_id": None,
        "change_threshold": None, "diffing_remaster": False,
        "diffed_against_sis_batch_id": None, "batch_mode": False, "batch_mode_term_id": None,
        "multi_term_batch_mode": False, "skip_deletes": False, "override_sis_stickiness": False,
        "add_sis_stickiness": False, "clear_sis_stickiness": False,
    })

    # content_migrations
    if course_list:
        rows["content_migrations"].append({
            "id": ids.next("content_migrations"),
            "created_at": _dt(now - timedelta(days=60)),
            "updated_at": _dt(now - timedelta(days=60)), "workflow_state": "imported",
            "context_id": rng.choice(course_list), "context_type": "Course",
            "user_id": rng.choice(teacher_pool) if teacher_pool else None,
            "migration_type": "canvas_cartridge_importer",
            "started_at": _dt(now - timedelta(days=60)),
            "finished_at": _dt(now - timedelta(days=59)),
            "migration_settings": None, "child_subscription_id": None, "source_course_id": None,
        })

    # media_objects
    if user_list:
        mo_id = "1_" + "".join(rng.choices(string.ascii_lowercase + string.digits, k=8))
        rows["media_objects"].append({
            "id": mo_id, "created_at": _dt(now - timedelta(days=90)),
            "updated_at": _dt(now - timedelta(days=90)), "workflow_state": "ready",
            "user_id": rng.choice(user_list),
            "context_id": rng.choice(course_list) if course_list else None,
            "context_type": "Course", "title": "Lecture Recording",
            "media_id": mo_id, "media_type": "video", "duration": rng.randint(300, 5400),
            "root_account_id": root_account_id,
        })
        reg.register("canvas.media_objects", mo_id)

    # conversations + messages + participants
    if len(user_list) >= 2:
        for _ in range(min(5, len(user_list) // 3)):
            conv_id = ids.next("conversations")
            participants = rng.sample(user_list, 2)
            last_msg = _dt(now - timedelta(days=rng.randint(1, 30)))
            rows["conversations"].append({
                "id": conv_id, "created_at": last_msg, "updated_at": last_msg,
                "workflow_state": "read", "last_message_at": last_msg,
                "message_count": 1, "private_hash": new_uuid()[:16],
                "subject": fake.sentence(nb_words=4),
                "context_id": rng.choice(course_list) if course_list else None,
                "context_type": "Course", "tags": None,
            })
            reg.register("canvas.conversations", conv_id)
            msg_id = ids.next("conversation_messages")
            rows["conversation_messages"].append({
                "id": msg_id, "created_at": last_msg, "updated_at": last_msg,
                "workflow_state": "active", "conversation_id": conv_id,
                "author_id": participants[0], "generated": False,
                "media_comment_id": None, "media_comment_type": None,
                "forwarded_message_ids": None,
                "body": fake.sentence(nb_words=15),
            })
            reg.register("canvas.conversation_messages", msg_id)
            for uid in participants:
                rows["conversation_participants"].append({
                    "id": ids.next("conversation_participants"),
                    "created_at": last_msg, "updated_at": last_msg,
                    "workflow_state": "read", "conversation_id": conv_id, "user_id": uid,
                    "subscribed": True, "label": None, "tags": None,
                    "last_message_at": last_msg, "message_count": 1,
                    "last_authored_at": last_msg, "visible_last_authored_at": last_msg,
                })
                rows["conversation_message_participants"].append({
                    "id": ids.next("conversation_message_participants"),
                    "created_at": last_msg, "updated_at": last_msg, "workflow_state": "active",
                    "conversation_message_id": msg_id, "user_id": uid,
                    "conversation_id": conv_id, "author_id": participants[0], "tags": None,
                })

    # content_participation_counts + participations
    for suid in user_list[:min(len(user_list), 10)]:
        if course_list:
            rows["content_participation_counts"].append({
                "id": ids.next("content_participation_counts"),
                "created_at": _dt(now - timedelta(days=7)),
                "updated_at": _dt(now - timedelta(days=7)), "workflow_state": "active",
                "content_type": "Submission", "context_id": rng.choice(course_list),
                "context_type": "Course", "user_id": suid, "unread_count": rng.randint(0, 5),
            })
        if sub_list:
            rows["content_participations"].append({
                "id": ids.next("content_participations"),
                "created_at": _dt(now - timedelta(days=5)),
                "updated_at": _dt(now - timedelta(days=5)), "workflow_state": "read",
                "content_type": "Submission",
                "content_id": rng.choice(sub_list), "user_id": suid,
            })

    # content_shares
    if len(user_list) >= 2 and assign_list:
        rows["content_shares"].append({
            "id": ids.next("content_shares"), "created_at": _dt(now - timedelta(days=20)),
            "updated_at": _dt(now - timedelta(days=20)), "workflow_state": "active",
            "name": "Shared Assignment", "user_id": user_list[0],
            "sender_id": user_list[1], "content_type": "Assignment",
            "content_id": rng.choice(assign_list), "read_state": "unread",
        })

    # custom_gradebook_columns + data
    if course_list:
        cgc_id = ids.next("custom_gradebook_columns")
        cid = rng.choice(course_list)
        rows["custom_gradebook_columns"].append({
            "id": cgc_id, "created_at": _dt(now - timedelta(days=30)),
            "updated_at": _dt(now - timedelta(days=30)), "workflow_state": "active",
            "course_id": cid, "title": "Notes", "position": 1, "read_only": False,
            "teacher_notes": True,
        })
        reg.register("canvas.custom_gradebook_columns", cgc_id)
        for uid in user_list[:min(5, len(user_list))]:
            rows["custom_gradebook_column_data"].append({
                "id": ids.next("custom_gradebook_column_data"),
                "created_at": _dt(now - timedelta(days=20)),
                "updated_at": _dt(now - timedelta(days=20)), "workflow_state": "active",
                "custom_gradebook_column_id": cgc_id, "user_id": uid,
                "content": mess.maybe_null(fake.sentence(nb_words=5)),
            })

    # custom_grade_statuses
    rows["custom_grade_statuses"].append({
        "id": ids.next("custom_grade_statuses"),
        "created_at": _dt(now - timedelta(days=90)),
        "updated_at": _dt(now - timedelta(days=90)), "workflow_state": "active",
        "name": "Excused", "color": "#FFD700", "root_account_id": root_account_id,
        "created_by_id": rng.choice(teacher_pool) if teacher_pool else None,
    })

    # collaborations
    if user_list and course_list:
        rows["collaborations"].append({
            "id": ids.next("collaborations"), "created_at": _dt(now - timedelta(days=45)),
            "updated_at": _dt(now - timedelta(days=45)), "workflow_state": "active",
            "context_id": rng.choice(course_list), "context_type": "Course",
            "user_id": rng.choice(user_list), "title": "Group Google Doc",
            "description": None, "type": "GoogleDocCollaboration",
            "url": None, "collaboration_type": "google_drive", "document_id": new_uuid(),
        })

    # group_categories + groups + memberships
    if course_list:
        gcid = ids.next("group_categories")
        cid = rng.choice(course_list)
        rows["group_categories"].append({
            "id": gcid, "created_at": _dt(now - timedelta(days=60)),
            "updated_at": _dt(now - timedelta(days=60)), "workflow_state": "active",
            "name": "Project Groups", "context_id": cid, "context_type": "Course",
            "role": None, "group_limit": 4, "auto_leader": None,
            "allows_multiple_memberships": False, "self_signup": None,
            "sis_source_id": None, "sis_batch_id": None,
        })
        grp_id = ids.next("groups")
        rows["groups"].append({
            "id": grp_id, "created_at": _dt(now - timedelta(days=55)),
            "updated_at": _dt(now - timedelta(days=55)), "workflow_state": "available",
            "name": "Group 1", "context_id": cid, "context_type": "Course",
            "account_id": root_account_id, "group_category_id": gcid,
            "max_membership": 4, "sis_source_id": None, "sis_batch_id": None,
            "storage_quota": 104857600, "description": None, "join_level": "invitation_only",
            "avatar_attachment_id": None, "leader_id": None,
            "lti_context_id": new_uuid(), "is_public": False, "default_view": "feed",
        })
        reg.register("canvas.groups", grp_id)
        students_in = student_ids_by_course.get(cid, user_list)
        for uid in students_in[:min(4, len(students_in))]:
            rows["group_memberships"].append({
                "id": ids.next("group_memberships"),
                "created_at": _dt(now - timedelta(days=50)),
                "updated_at": _dt(now - timedelta(days=50)),
                "workflow_state": "accepted", "user_id": uid, "group_id": grp_id,
                "moderator": False, "sis_batch_id": None,
            })

    # originality_reports
    if sub_list:
        rows["originality_reports"].append({
            "id": ids.next("originality_reports"),
            "created_at": _dt(now - timedelta(days=20)),
            "updated_at": _dt(now - timedelta(days=20)), "workflow_state": "scored",
            "submission_id": rng.choice(sub_list),
            "attachment_id": rng.choice(att_ids) if att_ids else None,
            "originality_score": round(rng.uniform(0, 40), 1),
            "originality_report_attachment_id": None, "originality_report_url": None,
            "submission_time": _dt(now - timedelta(days=20)),
            "root_account_id": root_account_id, "link_id": None, "error_message": None,
            "submission_type": "online_upload",
        })

    # canvadocs_annotation_contexts
    if att_ids and sub_list:
        rows["canvadocs_annotation_contexts"].append({
            "id": ids.next("canvadocs_annotation_contexts"),
            "created_at": _dt(now - timedelta(days=15)),
            "updated_at": _dt(now - timedelta(days=15)), "workflow_state": "active",
            "attachment_id": rng.choice(att_ids), "submission_id": rng.choice(sub_list),
            "root_account_id": root_account_id, "launch_id": new_uuid(),
        })

    # user_observation_links
    if len(user_list) >= 4:
        rows["user_observation_links"].append({
            "id": ids.next("user_observation_links"),
            "created_at": _dt(now - timedelta(days=200)),
            "updated_at": _dt(now - timedelta(days=200)), "workflow_state": "active",
            "student_id": user_list[0], "observer_id": user_list[-1],
            "root_account_id": root_account_id,
        })

    # user_notes
    if user_list and teacher_pool:
        rows["user_notes"].append({
            "id": ids.next("user_notes"), "created_at": _dt(now - timedelta(days=30)),
            "updated_at": _dt(now - timedelta(days=30)), "workflow_state": "active",
            "user_id": user_list[0],
            "created_by_id": rng.choice(teacher_pool),
            "note": "Student is struggling with module 2 assignments.",
            "title": "Progress Note",
        })

    # access_tokens
    if user_list and dk_ids:
        rows["access_tokens"].append({
            "id": ids.next("access_tokens"), "created_at": _dt(now - timedelta(days=60)),
            "updated_at": _dt(now - timedelta(days=60)), "workflow_state": "active",
            "user_id": rng.choice(user_list), "developer_key_id": dk_ids[0],
            "token_hint": "abc12", "expires_at": _dt(now + timedelta(days=30)),
            "purpose": "API access", "last_used_at": _dt(now - timedelta(days=1)), "scopes": None,
        })

    # assessment_question_banks + questions
    aqb_id = ids.next("assessment_question_banks")
    rows["assessment_question_banks"].append({
        "id": aqb_id, "created_at": _dt(now - timedelta(days=90)),
        "updated_at": _dt(now - timedelta(days=90)), "workflow_state": "active",
        "context_id": root_account_id, "context_type": "Account",
        "title": "Question Bank 1", "migration_id": None,
    })
    reg.register("canvas.assessment_question_banks", aqb_id)
    for n in range(5):
        rows["assessment_questions"].append({
            "id": ids.next("assessment_questions"),
            "created_at": _dt(now - timedelta(days=90)),
            "updated_at": _dt(now - timedelta(days=90)),
            "workflow_state": "active", "name": f"Question {n+1}",
            "context_id": root_account_id, "context_type": "Account",
            "assessment_question_bank_id": aqb_id,
            "question_data": json.dumps({"question_type": "multiple_choice_question", "points_possible": 1}),
            "migration_id": None,
        })

    # usage_rights
    if course_list:
        rows["usage_rights"].append({
            "id": ids.next("usage_rights"), "created_at": _dt(now - timedelta(days=90)),
            "updated_at": _dt(now - timedelta(days=90)), "workflow_state": "active",
            "use_justification": "own_copyright", "license": "private",
            "license_name": "All Rights Reserved",
            "context_id": rng.choice(course_list), "context_type": "Course", "legal_copyright": None,
        })

    # role_overrides
    if reg.ids("canvas.roles"):
        rows["role_overrides"].append({
            "id": ids.next("role_overrides"), "created_at": _dt(now - timedelta(days=200)),
            "updated_at": _dt(now - timedelta(days=200)), "workflow_state": "active",
            "permission": "read_as_admin_public_toall", "role_id": role_ids["TeacherEnrollment"],
            "account_id": root_account_id, "context_id": root_account_id,
            "context_type": "Account", "enabled": True, "locked": False,
            "applies_to_self": True, "applies_to_descendants": True, "applies_to_enrolled_users": None,
        })

    # accessibility_issues + resource_scans
    if course_list:
        cid = rng.choice(course_list)
        scan_id = ids.next("accessibility_resource_scans")
        rows["accessibility_resource_scans"].append({
            "id": scan_id, "created_at": _dt(now - timedelta(days=7)),
            "updated_at": _dt(now - timedelta(days=7)), "workflow_state": "completed",
            "context_id": cid, "context_type": "Course",
            "num_issues": rng.randint(0, 10),
            "last_scanned_at": _dt(now - timedelta(days=7)),
        })
        if rng.random() < 0.5:
            rows["accessibility_issues"].append({
                "id": ids.next("accessibility_issues"),
                "created_at": _dt(now - timedelta(days=7)),
                "updated_at": _dt(now - timedelta(days=7)), "workflow_state": "active",
                "content_id": rng.choice(assign_list) if assign_list else cid,
                "content_type": "Assignment", "course_id": cid,
                "rule_id": "adjacent-links", "display_name": "Adjacent link",
                "issue_url": None, "scan_id": scan_id,
            })

    # enrollment_dates_overrides
    if term_ids:
        rows["enrollment_dates_overrides"].append({
            "id": ids.next("enrollment_dates_overrides"),
            "created_at": _dt(now - timedelta(days=300)),
            "updated_at": _dt(now - timedelta(days=300)), "workflow_state": "active",
            "context_id": rng.choice(term_ids), "context_type": "EnrollmentTerm",
            "enrollment_type": "StudentEnrollment",
            "start_at": _dt(term_date_ranges[0][0]),
            "end_at": _dt(term_date_ranges[0][1]),
        })

    # assignment_overrides + override_students
    if assign_list:
        ao_id = ids.next("assignment_overrides")
        aid = rng.choice(assign_list)
        rows["assignment_overrides"].append({
            "id": ao_id, "created_at": _dt(now - timedelta(days=10)),
            "updated_at": _dt(now - timedelta(days=10)), "workflow_state": "active",
            "assignment_id": aid, "assignment_version": None, "set_type": "ADHOC",
            "set_id": None, "title": "Extended Deadline", "due_at": _dt(now + timedelta(days=3)),
            "due_at_overridden": True, "unlock_at": None, "unlock_at_overridden": False,
            "lock_at": None, "lock_at_overridden": False, "all_day": False, "all_day_date": None,
            "quiz_id": None, "quiz_version": None,
        })
        reg.register("canvas.assignment_overrides", ao_id)
        if user_list:
            rows["assignment_override_students"].append({
                "id": ids.next("assignment_override_students"),
                "created_at": _dt(now - timedelta(days=10)),
                "updated_at": _dt(now - timedelta(days=10)), "workflow_state": "active",
                "user_id": rng.choice(user_list), "assignment_id": aid,
                "assignment_override_id": ao_id, "quiz_id": None,
            })

    # learning_outcome_question_results
    lo_result_ids = [r["id"] for r in rows.get("learning_outcome_results", [])]
    if lo_result_ids:
        rows["learning_outcome_question_results"].append({
            "id": ids.next("learning_outcome_question_results"),
            "created_at": _dt(now - timedelta(days=30)),
            "updated_at": _dt(now - timedelta(days=30)), "workflow_state": "active",
            "learning_outcome_result_id": lo_result_ids[0],
            "associated_asset_id": None, "associated_asset_type": None,
            "score": rng.uniform(0, 4), "possible": 4.0, "mastery": rng.random() > 0.3,
            "percent": rng.uniform(0, 1), "attempt": 1, "title": "Q1",
            "original_score": rng.uniform(0, 4), "original_possible": 4.0,
            "original_mastery": rng.random() > 0.3, "assessed_at": _dt(now - timedelta(days=30)),
        })

    return rows
