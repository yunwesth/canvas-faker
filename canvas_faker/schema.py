"""Canvas Data 2 (CD2) schema, encoded as the single source of truth.

Each table is a list of column specs written in a compact DSL so the whole CD2
schema stays readable. A spec is ``"name:code"`` with an optional ``?`` suffix
marking the column nullable.

Type codes
----------
``pk``      int64 primary key, assigned by the IdAllocator
``strpk``   string primary key (e.g. Kaltura media id), generated
``uuidpk``  uuid string primary key (e.g. web_logs.id)
``int``     INTEGER (covers int32/int64)
``f``       REAL   (float64)
``bool``    INTEGER 0/1
``dt``      datetime, stored as ISO-8601 TEXT
``date``    date, stored as TEXT
``str``     TEXT
``json``    TEXT holding a JSON-encoded value (e.g. list[str])
``uuid``    uuid string TEXT
``@ns.tbl`` INTEGER foreign key referencing ``ns.tbl``'s primary key

Source: the ``canvas-data-2`` skill schema reference
(https://developerdocs.instructure.com/services/dap).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    name: str
    code: str            # normalized type code (see module docstring)
    nullable: bool
    fk: str | None       # "namespace.table" when this is a foreign key
    is_pk: bool

    @property
    def sqlite_type(self) -> str:
        return _SQLITE_TYPE.get(self.code, "TEXT")


_SQLITE_TYPE = {
    "pk": "INTEGER",
    "strpk": "TEXT",
    "uuidpk": "TEXT",
    "int": "INTEGER",
    "f": "REAL",
    "bool": "INTEGER",
    "dt": "TEXT",
    "date": "TEXT",
    "str": "TEXT",
    "json": "TEXT",
    "uuid": "TEXT",
    "fk": "INTEGER",
}

_PK_CODES = {"pk", "strpk", "uuidpk"}


def _parse_col(spec: str) -> Column:
    name, _, rawcode = spec.partition(":")
    nullable = rawcode.endswith("?")
    code = rawcode[:-1] if nullable else rawcode
    fk = None
    if code.startswith("@"):
        fk = code[1:]
        code = "fk"
    is_pk = code in _PK_CODES
    return Column(name=name, code=code, nullable=nullable, fk=fk, is_pk=is_pk)


# Common column prefixes shared by most canvas tables.
_BASE = ["id:pk", "created_at:dt", "updated_at:dt", "workflow_state:str"]


def _t(*extra: str, base=True) -> list[str]:
    return (_BASE if base else []) + list(extra)


# --------------------------------------------------------------------------- #
# Namespace: canvas
# --------------------------------------------------------------------------- #
CANVAS: dict[str, list[str]] = {
    "access_tokens": _t(
        "user_id:@canvas.users", "developer_key_id:@canvas.developer_keys",
        "token_hint:str?", "expires_at:dt?", "purpose:str?",
        "last_used_at:dt?", "scopes:str?"),
    "accessibility_issues": _t(
        "content_id:int", "content_type:str", "course_id:@canvas.courses?",
        "rule_id:str?", "display_name:str?", "issue_url:str?", "scan_id:int?"),
    "accessibility_resource_scans": _t(
        "context_id:int", "context_type:str", "num_issues:int?",
        "last_scanned_at:dt?"),
    "account_users": _t(
        "account_id:@canvas.accounts", "user_id:@canvas.users",
        "role_id:@canvas.roles", "sis_batch_id:int?"),
    "accounts": _t(
        "name:str?", "parent_account_id:int?", "root_account_id:int?",
        "sis_source_id:str?", "sis_batch_id:int?", "integration_id:str?",
        "lti_guid:str?", "uuid:uuid?", "default_storage_quota:int?",
        "default_user_storage_quota:int?", "default_group_storage_quota:int?",
        "default_time_zone:str?"),
    "assessment_question_banks": _t(
        "context_id:int?", "context_type:str?", "title:str?", "migration_id:str?"),
    "assessment_questions": _t(
        "name:str?", "context_id:int?", "context_type:str?",
        "assessment_question_bank_id:int?", "question_data:str?", "migration_id:str?"),
    "assignment_groups": _t(
        "name:str?", "context_id:int", "context_type:str", "group_weight:f?",
        "rules:str?", "sis_source_id:str?", "integration_data:str?", "position:int?"),
    "assignment_override_students": _t(
        "user_id:@canvas.users", "assignment_id:@canvas.assignments?",
        "assignment_override_id:@canvas.assignment_overrides", "quiz_id:int?"),
    "assignment_overrides": _t(
        "assignment_id:@canvas.assignments?", "assignment_version:int?",
        "set_type:str?", "set_id:int?", "title:str", "due_at:dt?",
        "due_at_overridden:bool", "unlock_at:dt?", "unlock_at_overridden:bool",
        "lock_at:dt?", "lock_at_overridden:bool", "all_day:bool", "all_day_date:date?",
        "quiz_id:int?", "quiz_version:int?"),
    "assignments": _t(
        "title:str?", "description:str?", "context_id:int", "context_type:str",
        "assignment_group_id:int?", "grading_type:str?", "points_possible:f?",
        "due_at:dt?", "unlock_at:dt?", "lock_at:dt?", "submission_types:json",
        "grading_standard_id:int?", "allowed_extensions:str?", "peer_reviews:bool",
        "automatic_peer_reviews:bool", "peer_review_count:int?", "peer_reviews_due_at:dt?",
        "peer_reviews_assigned:bool", "moderated_grading:bool", "grades_published_at:dt?",
        "grader_count:int?", "anonymous_grading:bool?", "omit_from_final_grade:bool",
        "position:int?", "migration_id:str?", "only_visible_to_overrides:bool",
        "post_to_sis:bool", "sis_source_id:str?", "integration_id:str?",
        "allowed_attempts:int?", "has_sub_assignments:bool?", "important_dates:bool",
        "duplicate_of_id:int?", "lti_context_id:str?", "turnitin_enabled:bool",
        "vericite_enabled:bool", "anonymous_instructor_annotations:bool",
        "annotatable_attachment_id:int?", "could_be_locked:bool", "freeze_on_copy:bool",
        "group_category_id:int?", "grade_group_students_individually:bool",
        "intra_group_peer_reviews:bool", "final_grader_id:int?", "grader_section_id:int?",
        "grader_names_visible_to_final_grader:bool?", "graders_anonymous_to_graders:bool?",
        "grader_comments_visible_to_graders:bool?", "parent_assignment_id:int?"),
    "attachment_associations": [
        "id:pk", "created_at:dt", "updated_at:dt",
        "attachment_id:@canvas.attachments", "context_id:int", "context_type:str"],
    "attachments": _t(
        "context_id:int?", "context_type:str?", "folder_id:int?", "user_id:int?",
        "filename:str?", "content_type:str?", "size:int?", "display_name:str?",
        "file_state:str?", "media_entry_id:str?", "could_be_locked:bool?", "locked:bool",
        "locked_for_user:bool?", "category:str?", "usage_rights_id:int?",
        "visibility_level:str?", "migration_id:str?"),
    "calendar_events": _t(
        "title:str?", "description:str?", "start_at:dt?", "end_at:dt?",
        "context_id:int", "context_type:str", "user_id:int?", "all_day:bool",
        "all_day_date:date?", "location_name:str?", "location_address:str?",
        "child_event_data:str?", "parent_calendar_event_id:int?",
        "effective_context_code:str?", "migration_id:str?", "important_dates:bool?"),
    "canvadocs_annotation_contexts": _t(
        "attachment_id:@canvas.attachments", "submission_id:@canvas.submissions?",
        "root_account_id:@canvas.accounts?", "launch_id:str?"),
    "collaborations": _t(
        "context_id:int", "context_type:str", "user_id:@canvas.users?", "title:str?",
        "description:str?", "type:str?", "url:str?", "collaboration_type:str?",
        "document_id:str?"),
    "comment_bank_items": _t(
        "course_id:@canvas.courses", "user_id:@canvas.users", "comment:str"),
    "communication_channels": _t(
        "user_id:@canvas.users", "path_type:str", "path:str", "position:int?",
        "bounce_count:int?", "last_bounce_at:dt?"),
    "content_migrations": _t(
        "context_id:int", "context_type:str", "user_id:int?", "migration_type:str?",
        "started_at:dt?", "finished_at:dt?", "migration_settings:str?",
        "child_subscription_id:int?", "source_course_id:int?"),
    "content_participation_counts": _t(
        "content_type:str", "context_id:int", "context_type:str",
        "user_id:@canvas.users", "unread_count:int"),
    "content_participations": _t(
        "content_type:str", "content_id:int", "user_id:@canvas.users"),
    "content_shares": _t(
        "name:str?", "user_id:@canvas.users", "sender_id:int?", "content_type:str",
        "content_id:int", "read_state:str?"),
    "content_tags": _t(
        "context_id:int?", "context_type:str?", "content_id:int?", "content_type:str?",
        "context_module_id:int?", "tag_type:str?", "title:str?", "url:str?",
        "position:int?", "indent:int?", "migration_id:str?", "learning_outcome_id:int?",
        "rubric_association_id:int?", "mastery_score:f?", "completion_requirement:str?",
        "associated_asset_id:int?", "associated_asset_type:str?", "new_tab:bool?",
        "external_url:str?"),
    "context_external_tools": _t(
        "context_id:int", "context_type:str", "name:str", "tool_id:str?", "domain:str?",
        "url:str?", "consumer_key:str?", "privacy_level:str?", "settings:str?",
        "migration_id:str?", "developer_key_id:int?", "root_account_id:@canvas.accounts",
        "lti_version:str?"),
    "context_module_progressions": _t(
        "context_module_id:@canvas.context_modules", "user_id:@canvas.users",
        "requirements_met:str?", "current_position:int?", "completed_at:dt?",
        "current:bool?", "lock_version:int", "evaluated_at:dt?"),
    "context_modules": _t(
        "context_id:int", "context_type:str", "name:str?", "position:int?",
        "unlock_at:dt?", "completion_requirements:str?", "prerequisites:str?",
        "require_sequential_progress:bool", "migration_id:str?"),
    "conversation_message_participants": _t(
        "conversation_message_id:@canvas.conversation_messages", "user_id:@canvas.users",
        "conversation_id:@canvas.conversations", "author_id:int", "tags:str?"),
    "conversation_messages": _t(
        "conversation_id:@canvas.conversations", "author_id:@canvas.users",
        "generated:bool", "media_comment_id:str?", "media_comment_type:str?",
        "forwarded_message_ids:str?", "body:str?"),
    "conversation_participants": _t(
        "conversation_id:@canvas.conversations", "user_id:@canvas.users",
        "subscribed:bool", "label:str?", "tags:str?", "last_message_at:dt?",
        "message_count:int", "last_authored_at:dt?", "visible_last_authored_at:dt?"),
    "conversations": _t(
        "last_message_at:dt?", "message_count:int", "private_hash:str?", "subject:str?",
        "context_id:int?", "context_type:str?", "tags:str?"),
    "course_account_associations": [
        "id:pk", "created_at:dt", "updated_at:dt", "course_id:@canvas.courses",
        "account_id:@canvas.accounts", "course_section_id:int?", "depth:int"],
    "course_sections": _t(
        "name:str", "course_id:@canvas.courses", "root_account_id:@canvas.accounts",
        "enrollment_term_id:int?", "sis_source_id:str?", "sis_batch_id:int?",
        "integration_id:str?", "start_at:dt?", "end_at:dt?",
        "restrict_enrollments_to_section_dates:bool?", "nonxlist_course_id:int?",
        "stuck_sis_fields:str?"),
    "courses": _t(
        "name:str?", "account_id:@canvas.accounts", "root_account_id:@canvas.accounts",
        "enrollment_term_id:int?", "sis_source_id:str?", "sis_batch_id:int?",
        "integration_id:str?", "course_code:str?", "default_view:str?", "license:str?",
        "start_at:dt?", "conclude_at:dt?", "grading_standard_id:int?", "is_public:bool?",
        "allow_student_wiki_edits:bool?", "is_public_to_auth_users:bool?",
        "public_syllabus:bool", "public_syllabus_to_auth:bool",
        "allow_student_forum_attachments:bool?", "open_enrollment:bool?",
        "self_enrollment:bool?", "restrict_enrollments_to_course_dates:bool?",
        "locale:str?", "time_zone:str?", "lti_context_id:str?", "storage_quota:int?",
        "uuid:uuid?", "show_announcements_on_home_page:bool?",
        "home_page_announcement_limit:int?", "homeroom_course:bool?", "template:bool?"),
    "custom_grade_statuses": _t(
        "name:str", "color:str?", "root_account_id:@canvas.accounts", "created_by_id:int?"),
    "custom_gradebook_column_data": _t(
        "custom_gradebook_column_id:@canvas.custom_gradebook_columns",
        "user_id:@canvas.users", "content:str?"),
    "custom_gradebook_columns": _t(
        "course_id:@canvas.courses", "title:str", "position:int", "read_only:bool",
        "teacher_notes:bool?"),
    "developer_key_account_bindings": _t(
        "account_id:@canvas.accounts", "developer_key_id:@canvas.developer_keys"),
    "developer_keys": _t(
        "name:str?", "user_id:int?", "email:str?", "redirect_uri:str?", "api_key:str?",
        "icon_url:str?", "account_id:int?", "visible:bool?", "is_lti_key:bool?",
        "public_jwk:str?", "public_jwk_url:str?", "scopes:str?",
        "client_credentials_audience:str?"),
    "discussion_entries": _t(
        "parent_id:int?", "discussion_topic_id:@canvas.discussion_topics",
        "user_id:@canvas.users?", "editor_id:int?", "message:str?", "rating_count:int?",
        "rating_sum:int?", "depth:int?", "root_entry_id:int?", "is_anonymous_author:bool?"),
    "discussion_entry_participants": [
        "id:pk", "created_at:dt", "updated_at:dt",
        "discussion_entry_id:@canvas.discussion_entries", "user_id:@canvas.users",
        "workflow_state:str", "rating:int?"],
    "discussion_topic_participants": [
        "id:pk", "created_at:dt", "updated_at:dt",
        "discussion_topic_id:@canvas.discussion_topics", "user_id:@canvas.users",
        "unread_entry_count:int", "workflow_state:str", "subscribed:bool?",
        "subscribed_timestamp:dt?"],
    "discussion_topics": _t(
        "title:str?", "message:str?", "context_id:int", "context_type:str",
        "user_id:int?", "assignment_id:int?", "attachment_id:int?", "discussion_type:str?",
        "lock_at:dt?", "last_reply_at:dt?", "posted_at:dt?", "delayed_post_at:dt?",
        "could_be_locked:bool", "position:int?", "is_announcement:bool", "pinned:bool?",
        "locked:bool?", "todo_date:dt?", "allow_rating:bool", "only_graders_can_rate:bool",
        "sort_by_rating:bool", "podcast_enabled:bool", "podcast_has_student_posts:bool",
        "require_initial_post:bool?", "migration_id:str?", "group_category_id:int?",
        "anonymous_state:str?"),
    "enrollment_dates_overrides": _t(
        "context_id:int?", "context_type:str?", "enrollment_type:str?",
        "start_at:dt?", "end_at:dt?"),
    "enrollment_states": [
        "enrollment_id:@canvas.enrollments", "state:str", "state_is_current:bool",
        "state_started_at:dt?", "state_valid_until:dt?", "restricted_access:bool",
        "access_is_current:bool"],
    "enrollment_terms": _t(
        "root_account_id:@canvas.accounts", "name:str?", "sis_source_id:str?",
        "sis_batch_id:int?", "integration_id:str?", "start_at:dt?", "end_at:dt?",
        "grading_period_group_id:int?"),
    "enrollments": _t(
        "user_id:@canvas.users", "course_id:@canvas.courses", "type:str",
        "course_section_id:@canvas.course_sections", "root_account_id:@canvas.accounts",
        "associated_user_id:int?", "role_id:@canvas.roles", "sis_source_id:str?",
        "sis_batch_id:int?", "integration_id:str?", "start_at:dt?", "end_at:dt?",
        "completed_at:dt?", "last_activity_at:dt?", "total_activity_time:int?",
        "grade_publishing_status:str?", "last_publish_attempt_at:dt?", "self_enrolled:bool?",
        "self_reported_grade:str?", "limit_privileges_to_course_section:bool",
        "peer_reviews_count:int?", "grades_submitted_at:dt?"),
    "favorites": [
        "id:pk", "created_at:dt", "updated_at:dt", "user_id:@canvas.users",
        "context_id:int", "context_type:str"],
    "folders": _t(
        "name:str?", "full_name:str?", "context_id:int", "context_type:str",
        "parent_folder_id:int?", "position:int?", "lock_at:dt?", "locked:bool",
        "hidden:bool?", "unlock_at:dt?", "submission_context_code:str?", "unique_type:str?"),
    "grading_period_groups": _t(
        "account_id:int?", "course_id:int?", "weighted:bool?",
        "display_totals_for_all_grading_periods:bool", "title:str?"),
    "grading_periods": _t(
        "grading_period_group_id:int", "title:str", "weight:f?", "start_date:dt",
        "end_date:dt", "close_date:dt"),
    "grading_standards": _t(
        "title:str", "data:str?", "context_id:int", "context_type:str",
        "context_code:str?", "version:int?", "user_id:int?", "root_account_id:int?",
        "migration_id:str?", "usage_count:int"),
    "group_categories": _t(
        "name:str?", "context_id:int", "context_type:str", "role:str?", "group_limit:int?",
        "auto_leader:str?", "allows_multiple_memberships:bool", "self_signup:str?",
        "sis_source_id:str?", "sis_batch_id:int?"),
    "group_memberships": _t(
        "user_id:@canvas.users", "group_id:@canvas.groups", "moderator:bool",
        "sis_batch_id:int?"),
    "groups": _t(
        "name:str?", "context_id:int", "context_type:str", "account_id:@canvas.accounts",
        "group_category_id:int?", "max_membership:int?", "sis_source_id:str?",
        "sis_batch_id:int?", "storage_quota:int", "description:str?", "join_level:str?",
        "avatar_attachment_id:int?", "leader_id:int?", "lti_context_id:str?",
        "is_public:bool", "default_view:str"),
    "late_policies": [
        "id:pk", "created_at:dt", "updated_at:dt", "course_id:@canvas.courses",
        "missing_submission_deduction_enabled:bool", "missing_submission_deduction:f",
        "late_submission_deduction_enabled:bool", "late_submission_deduction:f",
        "late_submission_interval:str", "late_submission_minimum_percent_enabled:bool",
        "late_submission_minimum_percent:f"],
    "learning_outcome_groups": _t(
        "context_id:int?", "context_type:str?", "title:str", "description:str?",
        "vendor_guid:str?", "root_account_id:@canvas.accounts",
        "root_learning_outcome_group_id:int?", "source_outcome_group_id:int?",
        "learning_outcome_group_id:int?", "migration_id:str?"),
    "learning_outcome_question_results": _t(
        "learning_outcome_result_id:int", "associated_asset_id:int?",
        "associated_asset_type:str?", "score:f?", "possible:f?", "mastery:bool?",
        "percent:f?", "attempt:int?", "title:str?", "original_score:f?",
        "original_possible:f?", "original_mastery:bool?", "assessed_at:dt?"),
    "learning_outcome_results": _t(
        "user_id:@canvas.users", "content_tag_id:@canvas.content_tags", "context_id:int",
        "context_type:str", "learning_outcome_id:@canvas.learning_outcomes",
        "association_id:int?", "association_type:str?", "artifact_id:int?",
        "artifact_type:str?", "score:f?", "possible:f?", "mastery:bool?", "percent:f?",
        "attempt:int?", "assessed_at:dt?", "submitted_or_assessed_at:dt?",
        "original_score:f?", "original_possible:f?", "original_mastery:bool?",
        "alignment_id:int?", "hide_points:bool", "hidden:bool",
        "learning_outcome_group_id:int?"),
    "learning_outcomes": _t(
        "context_id:int?", "context_type:str?", "short_description:str", "description:str?",
        "data:str?", "vendor_guid:str?", "root_account_id:@canvas.accounts", "title:str?",
        "migration_id:str?"),
    "lti_line_items": _t(
        "score_maximum:f", "label:str", "tag:str?", "resource_id:str?", "coupled:bool",
        "context_id:@canvas.courses", "resource_link_id:int?",
        "assignment_id:@canvas.assignments?", "client_id:int?", "lti_resource_link_id:int?",
        "lookup_id:str?", "extensions:str?"),
    "lti_resource_links": _t(
        "context_id:int", "context_type:str",
        "context_external_tool_id:@canvas.context_external_tools?", "custom:str?",
        "lookup_id:str", "resource_link_uuid:uuid"),
    "lti_results": _t(
        "line_item_id:@canvas.lti_line_items", "user_id:@canvas.users", "result_score:f?",
        "result_maximum:f?", "activity_progress:str?", "grading_progress:str?",
        "submission_id:@canvas.submissions?", "extensions:str?"),
    "media_objects": [
        "id:strpk", "created_at:dt", "updated_at:dt", "workflow_state:str", "user_id:int?",
        "context_id:int?", "context_type:str?", "title:str?", "media_id:str",
        "media_type:str?", "duration:int?", "root_account_id:@canvas.accounts?"],
    "originality_reports": _t(
        "submission_id:@canvas.submissions", "attachment_id:int?", "originality_score:f?",
        "originality_report_attachment_id:int?", "originality_report_url:str?",
        "submission_time:dt?", "root_account_id:@canvas.accounts?", "link_id:str?",
        "error_message:str?", "submission_type:str?"),
    "post_policies": _t(
        "post_manually:bool", "course_id:@canvas.courses?",
        "assignment_id:@canvas.assignments?"),
    "pseudonyms": _t(
        "user_id:@canvas.users", "account_id:@canvas.accounts", "unique_id:str",
        "sis_user_id:str?", "integration_id:str?", "sis_batch_id:int?",
        "authentication_provider_id:int?", "declared_user_type:str?"),
    "quiz_questions": _t(
        "quiz_id:@canvas.quizzes", "assessment_question_id:int?",
        "assessment_question_version:int?", "position:int?", "question_data:str?",
        "quiz_group_id:int?", "migration_id:str?"),
    "quiz_submissions": _t(
        "user_id:@canvas.users", "quiz_id:@canvas.quizzes",
        "submission_id:@canvas.submissions?", "score:f?", "kept_score:f?", "attempt:int?",
        "extra_attempts:int?", "extra_time:int?", "manually_scored:bool",
        "manually_unlocked:bool", "quiz_points_possible:f?", "score_before_regrade:f?",
        "fudge_points:f", "has_seen_results:bool", "was_preview:bool", "time_spent:int?",
        "end_at:dt?", "finished_at:dt?", "started_at:dt?"),
    "quizzes": _t(
        "title:str?", "description:str?", "due_at:dt?", "unlock_at:dt?", "lock_at:dt?",
        "points_possible:f?", "assignment_id:@canvas.assignments?",
        "context_id:@canvas.courses", "quiz_type:str", "assignment_group_id:int?",
        "shuffle_answers:bool", "show_correct_answers:bool", "time_limit:int?",
        "allowed_attempts:int?", "scoring_policy:str?", "access_code:str?", "ip_filter:str?",
        "anonymous_submissions:bool", "only_visible_to_overrides:bool",
        "one_question_at_a_time:bool", "cant_go_back:bool", "has_access_code:bool",
        "question_count:int", "unpublished_question_count:int", "could_be_locked:bool",
        "migration_id:str?"),
    "role_overrides": _t(
        "permission:str", "role_id:@canvas.roles", "account_id:@canvas.accounts",
        "context_id:int", "context_type:str", "enabled:bool?", "locked:bool",
        "applies_to_self:bool", "applies_to_descendants:bool",
        "applies_to_enrolled_users:bool?"),
    "roles": _t(
        "name:str", "label:str?", "base_role_type:str", "account_id:int?",
        "root_account_id:@canvas.accounts"),
    "rubric_assessments": _t(
        "rubric_id:@canvas.rubrics", "rubric_association_id:@canvas.rubric_associations?",
        "user_id:@canvas.users?", "assessor_id:@canvas.users", "artifact_id:int",
        "artifact_type:str", "data:str?", "score:f?", "assessment_type:str"),
    "rubric_associations": _t(
        "rubric_id:@canvas.rubrics", "association_id:int", "association_type:str",
        "context_id:int", "context_type:str", "use_for_grading:bool?", "purpose:str?",
        "summary_data:str?", "hide_score_total:bool?", "bookmarked:bool", "hide_points:bool?",
        "hide_outcome_results:bool?"),
    "rubrics": _t(
        "user_id:int?", "context_id:int", "context_type:str", "data:str?",
        "points_possible:f?", "title:str?", "description:str?", "reusable:bool",
        "read_only:bool", "free_form_criterion_comments:bool?", "hide_score_total:bool?",
        "will_overwrite_submissions:bool?", "migration_id:str?"),
    "scores": _t(
        "enrollment_id:@canvas.enrollments", "course_score:bool", "grading_period_id:int?",
        "current_score:f?", "final_score:f?", "unposted_current_score:f?",
        "unposted_final_score:f?", "override_score:f?", "current_grade:str?",
        "final_grade:str?", "unposted_current_grade:str?", "unposted_final_grade:str?",
        "override_grade:str?"),
    "sis_batches": _t(
        "account_id:@canvas.accounts", "ended_at:dt?", "data:str?", "progress:int?",
        "errors_attachment_id:int?", "user_id:int?", "change_threshold:int?",
        "diffing_remaster:bool", "diffed_against_sis_batch_id:int?", "batch_mode:bool?",
        "batch_mode_term_id:int?", "multi_term_batch_mode:bool?", "skip_deletes:bool",
        "override_sis_stickiness:bool", "add_sis_stickiness:bool", "clear_sis_stickiness:bool"),
    "submission_comments": _t(
        "submission_id:@canvas.submissions", "author_id:int?", "comment:str?",
        "attachment_ids:str?", "media_comment_id:str?", "media_comment_type:str?",
        "provisional_grade_id:int?", "anonymous:bool?", "hidden:bool", "attempt:int?",
        "group_comment_id:str?", "draft:bool"),
    "submissions": _t(
        "user_id:@canvas.users", "assignment_id:@canvas.assignments",
        "course_id:@canvas.courses", "submitted_at:dt?", "graded_at:dt?", "grader_id:int?",
        "score:f?", "grade:str?", "published_score:f?", "published_grade:str?",
        "submission_type:str?", "url:str?", "body:str?", "attempt:int?", "group_id:int?",
        "attachment_ids:str?", "grade_matches_current_submission:bool",
        "grading_period_id:int?", "late:bool", "missing:bool", "late_policy_status:str?",
        "seconds_late:int", "excused:bool?", "posted_at:dt?", "redo_request:bool",
        "cached_due_date:dt?", "resource_link_lookup_uuid:str?", "anonymous_id:str?",
        "extra_attempts:int?", "process_attempts:int"),
    "usage_rights": _t(
        "use_justification:str", "license:str", "license_name:str", "context_id:int?",
        "context_type:str?", "legal_copyright:str?"),
    "user_account_associations": [
        "id:pk", "created_at:dt", "updated_at:dt", "user_id:@canvas.users",
        "account_id:@canvas.accounts", "depth:int"],
    "user_notes": _t(
        "user_id:@canvas.users", "created_by_id:int?", "note:str?", "title:str?"),
    "user_observation_links": _t(
        "student_id:@canvas.users", "observer_id:@canvas.users",
        "root_account_id:@canvas.accounts"),
    "users": _t(
        "name:str?", "sortable_name:str?", "short_name:str?", "avatar_image_url:str?",
        "avatar_image_source:str?", "avatar_image_updated_at:dt?", "avatar_state:str?",
        "locale:str?", "time_zone:str?", "uuid:uuid", "school_name:str?",
        "school_position:int?", "storage_quota:int", "merged_into_user_id:int?",
        "lti_context_id:str?"),
    "wiki_pages": _t(
        "title:str?", "body:str?", "user_id:int?", "url:str", "context_id:int",
        "context_type:str", "wiki_id:int", "editing_roles:str?", "could_be_locked:bool",
        "todo_date:dt?", "published:bool", "publish_at:dt?"),
}


# --------------------------------------------------------------------------- #
# Namespace: canvas_logs
# --------------------------------------------------------------------------- #
CANVAS_LOGS: dict[str, list[str]] = {
    "web_logs": [
        "id:uuidpk", "timestamp:dt", "user_id:@canvas.users?", "real_user_id:@canvas.users?",
        "course_id:@canvas.courses?", "quiz_id:@canvas.quizzes?",
        "discussion_id:@canvas.discussion_topics?", "conversation_id:@canvas.conversations?",
        "assignment_id:@canvas.assignments?", "url:str", "http_method:str",
        "http_status:int", "http_version:str", "remote_ip:str", "interaction_micros:int",
        "web_application_controller:str?", "web_application_action:str?",
        "web_application_context_type:str?", "web_application_context_id:int?",
        "session_id:uuid?", "developer_key_id:@canvas.developer_keys?", "participated:bool",
        "user_agent:str?"],
}


# --------------------------------------------------------------------------- #
# Namespace: new_quizzes
# --------------------------------------------------------------------------- #
NEW_QUIZZES: dict[str, list[str]] = {
    "assessment_question_banks": [
        "id:pk", "created_at:dt", "updated_at:dt", "deleted_at:dt?", "workflow_state:str",
        "migration_id:str?", "title:str?"],
    "assessment_questions": [
        "id:pk", "name:str?", "created_at:dt", "updated_at:dt", "deleted_at:dt?",
        "workflow_state:str?", "context_id:int?", "context_type:str?", "migration_id:str?",
        "assessment_question_bank_id:int?", "question_data:str?", "position:int?",
        "item_id:int?"],
    "assignment_override_students": [
        "id:pk", "user_id:int?", "created_at:dt", "updated_at:dt", "workflow_state:str",
        "assignment_id:@new_quizzes.assignments?",
        "assignment_override_id:@new_quizzes.assignment_overrides"],
    "assignment_overrides": [
        "id:pk", "all_day:bool?", "all_day_date:date?", "assignment_id:@new_quizzes.assignments?",
        "assignment_version:int?", "created_at:dt", "due_at:dt?", "due_at_overridden:bool",
        "lock_at:dt?", "lock_at_overridden:bool", "quiz_id:@new_quizzes.quizzes?",
        "quiz_version:int?", "set_id:int?", "set_type:str?", "title:str", "unlock_at:dt?",
        "unlock_at_overridden:bool", "updated_at:dt", "workflow_state:str"],
    "assignments": [
        "id:pk", "integration_id:str?", "lti_context_id:str?", "created_at:dt?",
        "updated_at:dt?", "workflow_state:str", "due_at:dt?", "unlock_at:dt?", "lock_at:dt?",
        "points_possible:f?", "grading_type:str?", "submission_types:json",
        "assignment_group_id:int?", "grading_standard_id:int?", "peer_reviews:bool",
        "automatic_peer_reviews:bool", "moderated_grading:bool", "anonymous_grading:bool?",
        "omit_from_final_grade:bool", "only_visible_to_overrides:bool", "context_id:int?",
        "context_type:str", "allowed_attempts:int?", "position:int?", "title:str?",
        "has_sub_assignments:bool?", "parent_assignment_id:int?"],
    "quiz_questions": [
        "id:pk", "created_at:dt", "updated_at:dt", "archived_at:dt?", "workflow_state:str?",
        "quiz_id:@new_quizzes.quizzes", "migration_id:str?", "position:int?",
        "question_data:str?", "item_id:int?"],
    "quiz_submissions": [
        "id:pk", "user_id:int", "created_at:dt", "updated_at:dt", "workflow_state:str?",
        "quiz_id:@new_quizzes.quizzes", "started_at:dt?", "finished_at:dt?", "end_at:dt?",
        "score:f?", "attempt:int?", "submission_data:str?", "fudge_points:f",
        "quiz_points_possible:f?", "extra_attempts:int?", "extra_time:int?",
        "manually_scored:bool?", "was_preview:bool?", "has_seen_results:bool?"],
    "quizzes": [
        "id:pk", "created_at:dt", "updated_at:dt", "due_at:dt?", "unlock_at:dt?", "lock_at:dt?",
        "archived_at:dt?", "shuffle_answers:bool?", "title:str?", "workflow_state:str?",
        "description:str?", "time_limit:int?", "access_code:str?", "ip_filter:str?",
        "one_question_at_a_time:bool?", "cant_go_back:bool", "show_correct_answers:bool?",
        "hide_results:bool?", "practice_quiz:bool?", "context_id:int?", "context_type:str?",
        "migration_id:str?", "quiz_type:str", "points_possible:f?", "assignment_group_id:int?",
        "could_be_locked:bool?", "only_visible_to_overrides:bool?", "allowed_attempts:int?",
        "scoring_policy:str?", "anonymous_submissions:bool?", "assignment_id:int?"],
}


# --------------------------------------------------------------------------- #
# Namespace: catalog
#   The skill gives full columns for `certificates` and `enrollments`; the other
#   26 tables are documented only by column count, so we encode plausible,
#   schema-valid column sets (all carry id/created_at/updated_at/deleted_at).
# --------------------------------------------------------------------------- #
_CAT_BASE = ["id:pk", "created_at:dt", "updated_at:dt", "deleted_at:dt?"]

CATALOG: dict[str, list[str]] = {
    "account_admins": _CAT_BASE + [
        "account_id:@catalog.accounts", "canvas_user_id:int", "role:str", "active:bool"],
    "accounts": _CAT_BASE + [
        "name:str?", "parent_account_id:int?", "canvas_account_id:int?", "subdomain:str?",
        "theme_id:int?", "contact_email:str?", "time_zone:str?", "locale:str?",
        "visibility:str?", "active:bool", "listing_count:int?", "root_account:bool",
        "terms_of_service:str?", "privacy_policy:str?", "support_url:str?",
        "support_email:str?", "default_currency:str?", "tax_rate:f?", "enabled:bool",
        "canvas_domain:str?", "custom_css:str?"],
    "applicants": _CAT_BASE + [
        "product_id:@catalog.products", "user_id:@catalog.users", "status:str",
        "applied_at:dt?", "reviewed_at:dt?", "external_id:str?"],
    "bulk_checkout_promotions": ["id:pk", "created_at:dt",
        "bulk_checkout_id:@catalog.bulk_checkouts", "promotion_id:@catalog.promotions",
        "amount:f?", "code:str?"],
    "bulk_checkouts": _CAT_BASE + [
        "user_id:@catalog.users", "status:str", "total:f?", "seats:int?"],
    "bulk_invitations": _CAT_BASE + [
        "bulk_checkout_id:@catalog.bulk_checkouts", "email:str", "status:str",
        "sent_at:dt?", "redeemed_at:dt?", "token:str?"],
    "cart_item_promotions": ["id:pk", "created_at:dt",
        "cart_item_id:@catalog.cart_items", "promotion_id:@catalog.promotions",
        "amount:f?", "code:str?"],
    "cart_items": ["id:pk", "created_at:dt", "updated_at:dt",
        "cart_id:@catalog.carts", "product_id:@catalog.products"],
    "carts": _CAT_BASE + [
        "user_id:@catalog.users", "status:str", "subtotal:f?", "total:f?"],
    "categories": ["id:pk", "created_at:dt", "updated_at:dt",
        "account_id:@catalog.accounts", "name:str", "position:int?"],
    "certificate_templates": _CAT_BASE + [
        "account_id:@catalog.accounts", "name:str?", "template:str?", "active:bool"],
    "certificates": ["id:pk", "created_at:dt", "updated_at:dt", "deleted_at:dt?",
        "product_id:@catalog.products?", "name:str?",
        "certificate_template_id:@catalog.certificate_templates?",
        "custom_template_id:@catalog.certificate_templates?", "active:bool",
        "days_to_expire:int?", "expires_at:dt?", "old_template:str?", "old_pdf_settings:str?"],
    "custom_emails": _CAT_BASE + [
        "account_id:@catalog.accounts", "name:str?", "subject:str?", "body:str?",
        "email_layout_id:@catalog.email_layouts?", "active:bool", "kind:str?"],
    "email_layouts": ["id:pk", "created_at:dt", "updated_at:dt",
        "account_id:@catalog.accounts", "name:str?"],
    "enrollments": ["id:pk", "created_at:dt", "updated_at:dt", "deleted_at:dt?",
        "canvas_user_id:int", "product_id:@catalog.products", "root_program_id:int?",
        "order_item_id:@catalog.order_items?", "requirements_completed_at:dt?", "ends_at:dt?",
        "external_id:str?", "status:str", "last_sync_error:str?"],
    "order_item_promotions": ["id:pk", "created_at:dt",
        "order_item_id:@catalog.order_items", "promotion_id:@catalog.promotions",
        "amount:f?", "code:str?"],
    "order_items": ["id:pk", "created_at:dt", "updated_at:dt",
        "order_id:@catalog.orders", "product_id:@catalog.products", "quantity:int",
        "unit_price:f?", "subtotal:f?", "total:f?"],
    "orders": _CAT_BASE + [
        "user_id:@catalog.users", "status:str", "subtotal:f?", "tax:f?", "total:f?",
        "currency:str?", "external_id:str?"],
    "payments": _CAT_BASE + [
        "order_id:@catalog.orders", "amount:f?", "status:str", "gateway:str?"],
    "product_images": _CAT_BASE + [
        "product_id:@catalog.products", "url:str?", "position:int?", "alt_text:str?"],
    "product_tags": ["id:pk", "created_at:dt",
        "product_id:@catalog.products", "tag_id:@catalog.tags"],
    "products": _CAT_BASE + [
        "account_id:@catalog.accounts", "canvas_course_id:int?", "name:str?",
        "description:str?", "type:str?", "visibility:str?", "listing_state:str?",
        "price:f?", "currency:str?", "seat_count:int?", "waitlist:bool",
        "enrollment_open_at:dt?", "enrollment_close_at:dt?", "starts_at:dt?", "ends_at:dt?",
        "duration:str?", "position:int?", "featured:bool", "requires_application:bool",
        "external_id:str?", "sku:str?", "cover_image_url:str?", "thumbnail_url:str?",
        "slug:str?", "keywords:str?", "credits:f?", "level:str?", "language:str?",
        "instructor_name:str?", "canvas_account_id:int?", "root_program:bool",
        "program:bool", "certificate_enabled:bool"],
    "program_requirements": ["id:pk", "created_at:dt", "updated_at:dt",
        "program_id:@catalog.products", "required_product_id:@catalog.products",
        "position:int?", "required:bool"],
    "promotions": _CAT_BASE + [
        "account_id:@catalog.accounts", "name:str?", "code:str?", "kind:str?",
        "amount:f?", "percent:f?", "starts_at:dt?", "ends_at:dt?", "usage_limit:int?",
        "used_count:int?"],
    "tags": ["id:pk", "created_at:dt", "updated_at:dt",
        "account_id:@catalog.accounts", "name:str"],
    "themes": _CAT_BASE + [
        "account_id:@catalog.accounts", "name:str?", "primary_color:str?",
        "secondary_color:str?", "font:str?", "logo_url:str?", "favicon_url:str?",
        "custom_css:str?", "custom_js:str?", "active:bool", "header_html:str?"],
    "user_defined_fields": _CAT_BASE + [
        "account_id:@catalog.accounts", "label:str?", "field_type:str?", "required:bool",
        "position:int?", "options:str?", "active:bool"],
    "users": _CAT_BASE + [
        "canvas_user_id:int?", "name:str?", "email:str?", "time_zone:str?", "locale:str?",
        "last_login_at:dt?"],
}


NAMESPACES: dict[str, dict[str, list[str]]] = {
    "canvas": CANVAS,
    "canvas_logs": CANVAS_LOGS,
    "new_quizzes": NEW_QUIZZES,
    "catalog": CATALOG,
}


def parsed_table(namespace: str, table: str) -> list[Column]:
    """Return the parsed Column list for a namespace.table."""
    return [_parse_col(spec) for spec in NAMESPACES[namespace][table]]


def all_tables() -> list[tuple[str, str]]:
    """(namespace, table) pairs across every namespace."""
    return [(ns, tbl) for ns, tables in NAMESPACES.items() for tbl in tables]


def sqlite_table_name(namespace: str, table: str) -> str:
    return f"{namespace}__{table}"


def primary_key(columns: list[Column]) -> Column | None:
    for col in columns:
        if col.is_pk:
            return col
    return None
