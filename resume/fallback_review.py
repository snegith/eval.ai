from typing import Dict, List


def build_fallback_resume_review(profile: Dict[str, object], resume_text: str) -> Dict[str, object]:
    strengths: List[str] = []
    improvements: List[str] = []
    recommendations: List[str] = []

    summary = str(profile.get("summary") or "").strip()
    skills = profile.get("skills") or []
    experience = profile.get("experience") or []
    projects = profile.get("projects") or []
    education = profile.get("education") or []
    links = profile.get("links") or {}
    text_lower = (resume_text or "").lower()

    if summary and len(summary.split()) >= 10:
        strengths.append("The resume has a visible summary, which helps explain the candidate's direction quickly.")
    else:
        improvements.append("The resume would benefit from a clearer summary at the top.")
        recommendations.append("Add a short 2-3 line summary covering role focus, strongest skills, and impact.")

    if len(skills) >= 5:
        strengths.append("A meaningful set of skills is listed, which helps the profile scan faster.")
    else:
        improvements.append("The skills section looks limited or incomplete.")
        recommendations.append("Group the strongest tools by category such as languages, frameworks, cloud, and databases.")

    if experience:
        strengths.append("The resume includes identifiable experience entries, which gives the profile structure.")
    else:
        improvements.append("Work experience is not clearly communicated.")
        recommendations.append("Add role title, organization, dates, and outcome-focused bullets for each experience entry.")

    if projects:
        strengths.append("Projects are present, which is especially useful for technical screening.")
    else:
        improvements.append("A project section is missing or too weak to detect.")
        recommendations.append("Add 2-3 relevant projects with technologies used, what was built, and a concrete result.")

    if education:
        strengths.append("Education information is present, which helps anchor the background.")

    if links.get("github") or links.get("portfolio") or links.get("linkedin"):
        strengths.append("Professional links are included, which gives interviewers extra validation context.")
    else:
        improvements.append("No professional links were detected.")
        recommendations.append("Include LinkedIn and GitHub or portfolio links if they strengthen the profile.")

    if any(token in text_lower for token in ["%", "improved", "reduced", "increased", "built", "led", "developed"]):
        strengths.append("The resume uses some action-oriented language, which makes the content sound more impact-driven.")
    else:
        improvements.append("The resume could use more outcome-oriented and measurable language.")
        recommendations.append("Rewrite bullets to emphasize measurable outcomes, ownership, and scale.")

    score = 55
    score += min(15, len(skills) * 2)
    score += 10 if experience else -10
    score += 8 if projects else -6
    score += 5 if summary else -6
    score += 4 if links.get("github") or links.get("portfolio") else 0
    score = max(35, min(88, score))

    if score >= 80:
        label = "Strong"
    elif score >= 65:
        label = "Promising"
    else:
        label = "Needs Revision"

    return {
        "score": score,
        "label": label,
        "strengths": strengths[:5] or ["The resume contains enough structured information to support interview preparation."],
        "improvements": improvements[:5],
        "recommendations": recommendations[:5] or ["Tailor the resume more tightly to the target role before interviews."],
        "summary": "Fallback review generated from parsed resume structure because live LLM review was unavailable.",
        "_metadata": {
            "provider": "fallback",
            "model": "rule_based_fallback",
            "estimated_cost_usd": 0.0,
        },
    }
