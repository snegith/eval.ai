from __future__ import annotations

from typing import Any, Dict, List


def _clean_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    cleaned: List[str] = []
    for value in values:
        text = str(value or "").strip()
        if text:
            cleaned.append(text)
    return cleaned


def _entry_title(entry: Any) -> str:
    if isinstance(entry, dict):
        for key in ("title", "name", "role", "company", "institution"):
            text = str(entry.get(key) or "").strip()
            if text:
                return text
    return str(entry or "").strip()


def build_fallback_questions(profile: Dict[str, Any]) -> Dict[str, Any]:
    skills = _clean_list(profile.get("skills"))
    projects_raw = profile.get("projects") if isinstance(profile.get("projects"), list) else []
    experience_raw = profile.get("experience") if isinstance(profile.get("experience"), list) else []
    education_raw = profile.get("education") if isinstance(profile.get("education"), list) else []

    projects = [_entry_title(item) for item in projects_raw if _entry_title(item)]
    experience = [_entry_title(item) for item in experience_raw if _entry_title(item)]
    education = [_entry_title(item) for item in education_raw if _entry_title(item)]

    role_focus = "General Technical Interview"
    if any(skill.lower() in {"react", "javascript", "typescript", "next.js"} for skill in skills):
        role_focus = "Frontend / Full-Stack Interview"
    elif any(skill.lower() in {"python", "fastapi", "django", "flask", "sql"} for skill in skills):
        role_focus = "Backend / Software Engineering Interview"
    elif any(skill.lower() in {"machine learning", "tensorflow", "pytorch", "nlp"} for skill in skills):
        role_focus = "AI / Machine Learning Interview"

    questions: List[Dict[str, str]] = []

    top_skills = skills[:3] or ["your core technical stack"]
    for skill in top_skills[:2]:
        questions.append(
            {
                "category": "technical",
                "question": f"How have you used {skill} in a real project, and what tradeoffs did you have to make?",
                "rationale": f"Checks whether the candidate can move beyond listing {skill} and explain practical depth.",
            }
        )

    if skills:
        questions.append(
            {
                "category": "technical",
                "question": f"Which of these skills do you feel strongest in: {', '.join(top_skills)}? Walk me through a challenging problem you solved with it.",
                "rationale": "Tests technical ownership, problem-solving, and depth in the strongest area of the resume.",
            }
        )

    for project in projects[:2]:
        questions.append(
            {
                "category": "project",
                "question": f"Tell me about {project}. What was your role, what decisions did you make, and what would you improve if you rebuilt it?",
                "rationale": "Assesses ownership, architecture thinking, and ability to reflect on past work.",
            }
        )

    for role in experience[:2]:
        questions.append(
            {
                "category": "resume",
                "question": f"Looking at your experience in {role}, what impact are you most proud of, and how would you measure it?",
                "rationale": "Looks for outcome-focused storytelling instead of only task descriptions.",
            }
        )

    questions.append(
        {
            "category": "behavioral",
            "question": "Tell me about a time you had to learn something quickly to deliver on a project or deadline.",
            "rationale": "Evaluates adaptability, learning velocity, and communication under pressure.",
        }
    )
    questions.append(
        {
            "category": "behavioral",
            "question": "Describe a time you disagreed with a teammate or stakeholder. How did you handle it and what was the outcome?",
            "rationale": "Evaluates collaboration, maturity, and conflict resolution.",
        }
    )

    if education:
        questions.append(
            {
                "category": "follow_up",
                "question": f"How has your background in {education[0]} influenced the way you approach technical problems today?",
                "rationale": "Connects academic background to practical decision-making and communication.",
            }
        )

    deduped: List[Dict[str, str]] = []
    seen = set()
    for item in questions:
        question = item["question"].strip()
        if question and question not in seen:
            seen.add(question)
            deduped.append(item)

    if len(deduped) < 6:
        deduped.append(
            {
                "category": "follow_up",
                "question": "If I asked your teammates about your strongest contribution style, what would they say and why?",
                "rationale": "Adds a reflective prompt that surfaces teamwork patterns and self-awareness.",
            }
        )

    return {
        "role_focus": role_focus,
        "opening_prompt": "Walk me through the parts of your resume that best represent your strengths and the kind of work you want to do next.",
        "questions": deduped[:10],
        "_metadata": {
            "provider": "fallback",
            "model": "deterministic-profile-questions",
        },
    }
