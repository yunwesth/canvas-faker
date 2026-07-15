"""Custom Faker providers for Canvas-specific value shapes."""
from __future__ import annotations

import random
import string

from faker.providers import BaseProvider

DEPARTMENTS = [
    "BIOL", "CHEM", "PHYS", "MATH", "HIST", "ENGL", "PSYC", "SOC",
    "ECON", "CS", "ART", "MUSC", "SPAN", "FREN", "PHIL", "NURS",
    "BUS", "ACCT", "MKT", "COMM", "EDUC", "POLS", "ANTH", "GEOG",
]

COURSE_NAMES = [
    "Introduction to {dept}", "Advanced {dept}", "Topics in {dept}",
    "Principles of {dept}", "Survey of {dept}", "Foundations of {dept}",
    "Applied {dept}", "Research Methods in {dept}", "Seminar in {dept}",
    "History of {dept}", "Theory and Practice of {dept}",
]

DEPT_FULL = {
    "BIOL": "Biology", "CHEM": "Chemistry", "PHYS": "Physics",
    "MATH": "Mathematics", "HIST": "History", "ENGL": "English",
    "PSYC": "Psychology", "SOC": "Sociology", "ECON": "Economics",
    "CS": "Computer Science", "ART": "Art", "MUSC": "Music",
    "SPAN": "Spanish", "FREN": "French", "PHIL": "Philosophy",
    "NURS": "Nursing", "BUS": "Business", "ACCT": "Accounting",
    "MKT": "Marketing", "COMM": "Communications", "EDUC": "Education",
    "POLS": "Political Science", "ANTH": "Anthropology", "GEOG": "Geography",
}

ASSIGNMENT_TITLES = [
    "Homework {n}", "Lab Report {n}", "Essay {n}", "Problem Set {n}",
    "Reading Response {n}", "Case Study {n}", "Project {n}", "Quiz {n}",
    "Reflection Paper {n}", "Discussion Post {n}", "Research Paper {n}",
    "Midterm Exam", "Final Exam", "Group Project", "Presentation {n}",
]

QUIZ_TITLES = [
    "Quiz {n}: {topic}", "Unit {n} Assessment", "Chapter {n} Quiz",
    "Weekly Check-in {n}", "Knowledge Check {n}",
]

QUIZ_TOPICS = [
    "Key Concepts", "Core Vocabulary", "Main Themes", "Critical Analysis",
    "Problem Solving", "Foundational Principles", "Review", "Applications",
]

DISCUSSION_TITLES = [
    "Week {n} Discussion", "Introduction Thread", "Reflection on {topic}",
    "Debate: {topic}", "Share Your Thoughts: {topic}",
]

MODULE_NAMES = [
    "Module {n}: Introduction", "Unit {n}: Core Concepts",
    "Week {n}", "Chapter {n}", "Part {n}: Applications",
    "Section {n}: Review", "Topic {n}",
]

GRADER_COMMENTS = [
    "Good work overall, but could be more thorough.",
    "Excellent analysis! Clear and well-structured.",
    "Needs more evidence to support your claims.",
    "Late submission noted — see late policy.",
    "Please resubmit with proper citations.",
    "Strong argument, minor grammar issues.",
    "Missing the second section entirely.",
    "Well done! Exceeded expectations.",
    "Adequate work, room for improvement.",
    "See my notes in the margin for details.",
]

LETTER_GRADES = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F"]

SIS_ID_PREFIXES = ["SIS", "ERP", "BANNER", "PX", "STU"]

LTI_TOOLS = [
    ("Turnitin", "turnitin.com"),
    ("Kaltura", "kaltura.com"),
    ("Google Drive", "google.com"),
    ("VoiceThread", "voicethread.com"),
    ("Proctorio", "proctorio.com"),
    ("Panopto", "panopto.com"),
    ("Piazza", "piazza.com"),
    ("Gradescope", "gradescope.com"),
]

ACCOUNT_NAMES = [
    "College of Arts & Sciences", "School of Business", "School of Nursing",
    "College of Education", "School of Engineering", "Department of Mathematics",
    "Department of History", "Faculty Senate", "Graduate School",
    "Center for Online Learning", "Continuing Education",
]


class CanvasProvider(BaseProvider):

    def course_code(self, dept: str | None = None) -> str:
        dept = dept or self.random_element(DEPARTMENTS)
        number = self.random_element(["100", "101", "201", "202", "301", "401", "499"])
        section = self.random_element(["", "-01", "-H", "-W"])
        return f"{dept}-{number}{section}"

    def course_name(self, dept: str | None = None) -> str:
        dept = dept or self.random_element(DEPARTMENTS)
        tmpl = self.random_element(COURSE_NAMES)
        return tmpl.format(dept=DEPT_FULL.get(dept, dept))

    def sis_id(self, prefix: str | None = None) -> str:
        pfx = prefix or self.random_element(SIS_ID_PREFIXES)
        return f"{pfx}-{self.random_int(10000, 99999)}"

    def canvas_uuid(self) -> str:
        chars = string.ascii_letters + string.digits
        return "".join(self.random_choices(chars, length=43))

    def letter_grade(self, score_pct: float | None = None) -> str:
        if score_pct is None:
            return self.random_element(LETTER_GRADES)
        if score_pct >= 93: return "A"
        if score_pct >= 90: return "A-"
        if score_pct >= 87: return "B+"
        if score_pct >= 83: return "B"
        if score_pct >= 80: return "B-"
        if score_pct >= 77: return "C+"
        if score_pct >= 73: return "C"
        if score_pct >= 70: return "C-"
        if score_pct >= 67: return "D+"
        if score_pct >= 60: return "D"
        return "F"

    def assignment_title(self, n: int = 1) -> str:
        tmpl = self.random_element(ASSIGNMENT_TITLES)
        return tmpl.format(n=n)

    def quiz_title(self, n: int = 1) -> str:
        tmpl = self.random_element(QUIZ_TITLES)
        return tmpl.format(n=n, topic=self.random_element(QUIZ_TOPICS))

    def discussion_title(self, n: int = 1) -> str:
        from faker.providers import BaseProvider
        tmpl = self.random_element(DISCUSSION_TITLES)
        topic = self.random_element(QUIZ_TOPICS)
        return tmpl.format(n=n, topic=topic)

    def module_name(self, n: int = 1) -> str:
        tmpl = self.random_element(MODULE_NAMES)
        return tmpl.format(n=n)

    def grader_comment(self) -> str:
        return self.random_element(GRADER_COMMENTS)

    def lti_tool(self) -> tuple[str, str]:
        return self.random_element(LTI_TOOLS)

    def account_name(self) -> str:
        return self.random_element(ACCOUNT_NAMES)

    def sortable_name(self, full_name: str) -> str:
        parts = full_name.strip().rsplit(" ", 1)
        if len(parts) == 2:
            return f"{parts[1]}, {parts[0]}"
        return full_name

    def realistic_score(self, max_pts: float, mess_intensity: float = 0.3) -> float:
        """Normally-distributed score with occasional zeros/near-perfects."""
        rng = random.random()
        if rng < 0.02 * mess_intensity:
            return 0.0
        if rng < 0.04 * mess_intensity:
            return round(max_pts * random.uniform(0.05, 0.2), 1)
        pct = min(1.0, max(0.0, random.gauss(0.78, 0.14)))
        return round(max_pts * pct, 1)
