import re
from collections import Counter
from pathlib import Path
from typing import Dict, List


SECTION_ALIASES = {
    "summary": {"summary", "profile", "professional summary", "objective", "about"},
    "skills": {"skills", "technical skills", "core competencies", "technologies", "tech stack"},
    "experience": {"experience", "work experience", "professional experience", "employment", "employment history"},
    "projects": {"projects", "personal projects", "key projects", "academic projects"},
    "education": {"education", "academic background", "qualifications"},
    "certifications": {"certifications", "licenses", "certificates"},
}

COMMON_SKILL_TERMS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node",
    "fastapi",
    "django",
    "flask",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "git",
    "tensorflow",
    "pytorch",
    "opencv",
    "mediapipe",
    "streamlit",
    "html",
    "css",
    "tailwind",
    "c++",
    "c",
    "c#",
    "go",
    "rust",
    "pandas",
    "numpy",
    "scikit-learn",
    "linux",
}


def extract_text_from_resume(file_path: str) -> Dict[str, object]:
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_text(path)
    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return {
            "source_filename": path.name,
            "page_count": 1,
            "char_count": len(text),
            "full_text": _normalize_text(text),
        }
    raise ValueError(f"Unsupported resume format: {suffix}. Please upload a PDF or plain text resume.")


def parse_resume_text(resume_text: str) -> Dict[str, object]:
    cleaned_text = _normalize_text(resume_text)
    lines = [line.strip() for line in cleaned_text.splitlines() if line.strip()]
    sections = _split_sections(lines)

    profile = {
        "name": _extract_name(lines),
        "emails": sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", cleaned_text))),
        "phones": _extract_phones(cleaned_text),
        "links": _extract_links(cleaned_text),
        "summary": _extract_summary(lines, sections),
        "skills": _extract_skills(sections, cleaned_text),
        "experience": _extract_entries(sections.get("experience", [])),
        "projects": _extract_entries(sections.get("projects", [])),
        "education": _extract_entries(sections.get("education", [])),
        "certifications": _extract_entries(sections.get("certifications", [])),
        "raw_sections": sections,
        "keywords": _extract_keywords(cleaned_text),
        "parsing_warnings": [],
    }

    if not profile["name"]:
        profile["parsing_warnings"].append("Could not confidently identify the candidate name.")
    if not profile["skills"]:
        profile["parsing_warnings"].append("No structured skills section was detected.")
    if not profile["experience"]:
        profile["parsing_warnings"].append("No experience entries were detected.")

    return profile


def build_resume_artifacts(file_path: str) -> Dict[str, object]:
    extracted = extract_text_from_resume(file_path)
    profile = parse_resume_text(str(extracted["full_text"]))
    preview = extracted["full_text"][:1200]

    return {
        "resume_text": {
            "source_filename": extracted["source_filename"],
            "page_count": extracted["page_count"],
            "char_count": extracted["char_count"],
            "text_preview": preview,
            "full_text": extracted["full_text"],
        },
        "resume_profile": profile,
    }


def _extract_pdf_text(path: Path) -> Dict[str, object]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Resume PDF parsing requires the 'pypdf' package to be installed.") from exc

    reader = PdfReader(str(path))
    pages: List[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")

    text = _normalize_text("\n".join(pages))
    return {
        "source_filename": path.name,
        "page_count": len(reader.pages),
        "char_count": len(text),
        "full_text": text,
    }


def _normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _split_sections(lines: List[str]) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {key: [] for key in SECTION_ALIASES}
    current_section = "summary"

    for line in lines:
        normalized = re.sub(r"[^a-z ]", "", line.lower()).strip()
        matched = next(
            (key for key, aliases in SECTION_ALIASES.items() if normalized in aliases),
            None,
        )
        if matched:
            current_section = matched
            continue
        sections.setdefault(current_section, []).append(line)

    return sections


def _extract_name(lines: List[str]) -> str:
    for line in lines[:5]:
        cleaned = line.strip(" |,-")
        if len(cleaned.split()) > 5:
            continue
        if any(char.isdigit() for char in cleaned) or "@" in cleaned:
            continue
        if re.search(r"(linkedin|github|portfolio|resume|curriculum)", cleaned, flags=re.IGNORECASE):
            continue
        return cleaned
    return ""


def _extract_phones(text: str) -> List[str]:
    matches = re.findall(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4}", text)
    cleaned = []
    for match in matches:
        normalized = re.sub(r"\s+", " ", match).strip()
        if len(re.sub(r"\D", "", normalized)) >= 10:
            cleaned.append(normalized)
    return sorted(set(cleaned))


def _extract_links(text: str) -> Dict[str, List[str]]:
    urls = sorted(set(re.findall(r"https?://[^\s|)]+", text)))
    linkedin = [url for url in urls if "linkedin" in url.lower()]
    github = [url for url in urls if "github" in url.lower()]
    portfolio = [url for url in urls if url not in linkedin and url not in github]
    return {
        "linkedin": linkedin,
        "github": github,
        "portfolio": portfolio,
    }


def _extract_summary(lines: List[str], sections: Dict[str, List[str]]) -> str:
    summary_lines = sections.get("summary", [])
    if summary_lines:
        return " ".join(summary_lines[:4]).strip()

    paragraph = []
    for line in lines[1:8]:
        if "@" in line or re.search(r"https?://", line):
            continue
        paragraph.append(line)
    return " ".join(paragraph[:4]).strip()


def _extract_skills(sections: Dict[str, List[str]], text: str) -> List[str]:
    skills_lines = sections.get("skills", [])
    candidates: List[str] = []

    for line in skills_lines:
        normalized_line = line.replace("\u2022", ",").replace("|", ",").replace(";", ",")
        for chunk in normalized_line.split(","):
            item = chunk.strip(" :-")
            if 1 < len(item) <= 40:
                candidates.append(item)

    if not candidates:
        lowered = text.lower()
        candidates.extend(term for term in COMMON_SKILL_TERMS if term in lowered)

    deduped = []
    seen = set()
    for candidate in candidates:
        label = candidate.strip()
        key = label.lower()
        if not label or key in seen:
            continue
        seen.add(key)
        deduped.append(label)
    return deduped[:30]


def _extract_entries(lines: List[str]) -> List[str]:
    entries: List[str] = []
    current: List[str] = []

    for line in lines:
        bullet_like = line.startswith(("-", "*", "\u2022"))
        if bullet_like and current:
            current.append(line.lstrip("-*\u2022 ").strip())
            continue
        if current and _looks_like_new_entry(line):
            entries.append(" ".join(current).strip())
            current = [line]
            continue
        if not current:
            current = [line]
        else:
            current.append(line)

    if current:
        entries.append(" ".join(current).strip())
    return [entry for entry in entries if entry]


def _looks_like_new_entry(line: str) -> bool:
    if re.search(r"\b(19|20)\d{2}\b", line):
        return True
    words = line.split()
    return 1 < len(words) <= 8 and line == line.title()


def _extract_keywords(text: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#.-]{1,24}", text.lower())
    filtered = [token for token in tokens if token in COMMON_SKILL_TERMS]
    counts = Counter(filtered)
    return [token for token, _ in counts.most_common(15)]
