def derive_confidence_score(eye_contact, posture):
    """
    Derive confidence score from behavioral metrics.
    
    Confidence is primarily indicated by:
    - Eye contact (60% weight) - Direct gaze shows confidence
    - Posture (40% weight) - Upright posture shows confidence
    
    Uses damping factor to prevent saturation (nobody is 100% confident).
    
    Returns:
        float: Confidence score 0-95 (capped to maintain realism)
    """
    # Calculate raw confidence
    raw_confidence = (eye_contact * 0.6) + (posture * 0.4)
    
    # Apply damping and cap at 95
    confidence = min(95, raw_confidence * 0.9)
    
    return confidence


def derive_nervousness_score(consistency, stability):
    """
    Derive nervousness score from facial animation metrics.
    
    Nervousness is indicated by:
    - Low consistency (erratic expressions)
    - Low stability (jittery movements)
    
    Returns:
        float: Nervousness score 0-100 (higher = more nervous)
    """
    # Inverse of consistency and stability
    nervousness = 100 - ((consistency * 0.6) + (stability * 0.4))
    return max(0, min(100, nervousness))


def interpret_nervousness(nervousness):
    """
    Direct interpretation of nervousness score.
    
    Args:
        nervousness: Score 0-100 (higher = more nervous)
    
    Returns:
        str: Human-readable interpretation
    """
    if nervousness < 30:
        return "Calm and composed"
    elif nervousness < 50:
        return "Some nervous energy"
    else:
        return "Appears notably nervous"


def interpret_score(score, thresholds):
    """
    Interpret a score based on thresholds.
    
    Args:
        score: Numeric score
        thresholds: Dict with 'excellent', 'good', 'fair', 'poor' thresholds
    
    Returns:
        str: Interpretation label
    """
    if score >= thresholds.get('excellent', 80):
        return "Excellent"
    elif score >= thresholds.get('good', 65):
        return "Good"
    elif score >= thresholds.get('fair', 50):
        return "Fair"
    else:
        return "Needs Improvement"


def build_feedback_prompt(transcript: str, metrics: dict) -> str:
    """
    Builds a structured prompt for interview feedback generation.
    
    Args:
        transcript: Interview Q&A text
        metrics: Dictionary containing:
            - eye_contact: percentage (0-100)
            - eye_contact_grade: interpretation
            - posture: percentage (0-100)
            - posture_grade: interpretation
            - expressiveness: score (0-100)
            - consistency: score (0-100)
            - stability: score (0-100)
            - animation_grade: interpretation
            - peak_frequency: peaks per second
    
    Returns:
        str: Formatted prompt for LLM
    """
    
    # Validate transcript
    if not transcript or len(transcript.strip()) < 20:
        transcript = "[No transcript available - analysis based on behavioral metrics only]"
    
    # Extract metrics with defaults
    eye_contact = metrics.get('eye_contact', 0)
    eye_contact_grade = metrics.get('eye_contact_grade', 'Unknown')
    posture = metrics.get('posture', 0)
    posture_grade = metrics.get('posture_grade', 'Unknown')
    expressiveness = metrics.get('expressiveness', 0)
    consistency = metrics.get('consistency', 0)
    stability = metrics.get('stability', 0)
    animation_grade = metrics.get('animation_grade', 'Unknown')
    peak_frequency = metrics.get('peak_frequency', 0)
    
    # Prefer persisted derived metrics when available so prompt input matches UI/exported results.
    confidence = metrics.get('confidence_score')
    nervousness = metrics.get('nervousness_score')

    if confidence is None:
        confidence = derive_confidence_score(eye_contact, posture)
    if nervousness is None:
        nervousness = derive_nervousness_score(consistency, stability)
    
    # Interpret derived scores
    confidence_label = interpret_score(confidence, {
        'excellent': 70, 'good': 55, 'fair': 40
    })
    nervousness_label = interpret_nervousness(nervousness)
    
    prompt = f"""You are an experienced interview coach providing constructive feedback on a mock interview.

Your analysis should be:
- Honest but encouraging
- Specific with examples from the transcript
- Actionable with concrete improvement steps
- Balanced between strengths and areas for growth

=====================
INTERVIEW TRANSCRIPT
=====================
{transcript}

=====================
BEHAVIORAL METRICS
=====================

PRIMARY METRICS:
• Eye Contact: {eye_contact:.1f}% ({eye_contact_grade})
  - Context: Eye contact percentage indicates engagement and confidence
  - Benchmark: >75% excellent, 60-75% good, 45-60% fair, <45% needs improvement

• Posture: {posture:.1f}% ({posture_grade})
  - Context: Posture reflects professionalism and physical confidence
  - Benchmark: >75% excellent, 60-75% good, 45-60% fair, <45% needs improvement

• Facial Animation: {expressiveness:.1f}/100 expressiveness, {consistency:.1f}/100 consistency
  - Grade: {animation_grade}
  - Context: Expressiveness shows engagement; consistency indicates emotional control
  - Benchmark: 55-70 expressiveness with >70 consistency is ideal

DERIVED METRICS:
• Confidence Score: {confidence:.1f}/95 ({confidence_label})
  - Derived from: Eye contact (60%) + Posture (40%)
  - Context: Reflects perceived confidence through body language
  - Note: Capped at 95 for realism (perfect confidence is rare)

• Nervousness Indicator: {nervousness:.1f}/100 ({nervousness_label})
  - Derived from: Facial consistency (60%) + Stability (40%)
  - Context: Higher scores indicate more nervous behavior
  - Benchmark: <30 calm, 30-50 moderate, >50 notably nervous

ANIMATION DETAILS:
• Stability: {stability:.1f}/100
  - Context: Measures smoothness of facial movements
  - Benchmark: >85 very smooth, 70-85 moderate, <70 jittery
  
• Expressive Peaks: {peak_frequency:.2f} per second
  - Context: Frequency of animated moments during speech
  - Benchmark: 0.2-0.5 natural emphasis, >0.5 highly animated, <0.2 minimal variation

=====================
YOUR TASKS
=====================

Analyze both the CONTENT (transcript) and DELIVERY (behavioral metrics) to provide:

1. OVERALL SCORE (0-100 scale):
   - Content quality: 50% weight
   - Eye contact: 15% weight
   - Posture: 15% weight
   - Facial animation: 20% weight

2. KEY STRENGTHS (3-5 specific points):
   - Reference specific examples from transcript OR specific metrics
   - Be genuine - if something is truly strong, highlight it
   - Balance content and delivery strengths

3. AREAS FOR IMPROVEMENT (3-5 specific points):
   - Be constructive and specific
   - Prioritize highest-impact improvements
   - Include both content and delivery feedback

4. STAR METHOD EVALUATION (if applicable):
   - Detect if the response is answering a behavioral question
   - If yes, evaluate Situation, Task, Action, Result clarity (1-5 each)
   - If no, note that STAR is not applicable for this question type

5. ACTIONABLE RECOMMENDATIONS (3-5 concrete steps):
   - Specific actions the candidate can take
   - Prioritized by impact and ease of implementation
   - Include both content and delivery improvements

6. OVERALL SUMMARY (3-4 sentences):
   - High-level assessment of interview readiness
   - Balance encouragement with honest assessment
   - Mention 1-2 key takeaways

=====================
OUTPUT FORMAT
=====================

Return ONLY a valid JSON object with NO additional text, markdown, or code blocks.
The JSON must have this exact structure:

{{
  "overall_score": <number 0-100>,
  "score_breakdown": {{
    "content": <number 0-100>,
    "eye_contact": <number 0-100>,
    "posture": <number 0-100>,
    "animation": <number 0-100>
  }},
  "strengths": [
    "<specific strength with evidence>",
    "<specific strength with evidence>",
    "<specific strength with evidence>"
  ],
  "improvements": [
    "<specific improvement area with explanation>",
    "<specific improvement area with explanation>",
    "<specific improvement area with explanation>"
  ],
  "star_analysis": {{
    "applicable": <true/false>,
    "situation_score": <1-5 or null>,
    "task_score": <1-5 or null>,
    "action_score": <1-5 or null>,
    "result_score": <1-5 or null>,
    "overall_star_score": <1-5 or null>,
    "feedback": "<specific feedback on STAR usage or 'Not applicable'>"
  }},
  "recommendations": [
    "<specific actionable recommendation>",
    "<specific actionable recommendation>",
    "<specific actionable recommendation>"
  ],
  "summary": "<3-4 sentence overall assessment>"
}}

CRITICAL: Return ONLY the JSON. No explanations before or after. No markdown formatting."""

    return prompt


def validate_metrics(metrics: dict) -> dict:
    """
    Validate and normalize metrics dictionary.
    
    Args:
        metrics: Raw metrics dictionary
    
    Returns:
        dict: Validated and normalized metrics
    """
    required_keys = [
        'eye_contact', 'posture', 'expressiveness', 
        'consistency', 'stability'
    ]
    
    validated = {}
    
    for key in required_keys:
        if key not in metrics:
            raise ValueError(f"Missing required metric: {key}")
        
        value = metrics[key]
        if not isinstance(value, (int, float)):
            raise ValueError(f"Metric '{key}' must be numeric, got {type(value)}")
        
        if not (0 <= value <= 100):
            raise ValueError(f"Metric '{key}' must be 0-100, got {value}")
        
        validated[key] = float(value)
    
    # Copy optional keys
    optional_keys = [
        'eye_contact_grade', 'posture_grade', 'animation_grade',
        'peak_frequency', 'confidence_score', 'nervousness_score'
    ]
    
    for key in optional_keys:
        if key in metrics:
            validated[key] = metrics[key]

    for key, upper_bound in (('confidence_score', 95), ('nervousness_score', 100), ('peak_frequency', None)):
        if key not in validated:
            continue
        value = validated[key]
        if not isinstance(value, (int, float)):
            raise ValueError(f"Metric '{key}' must be numeric, got {type(value)}")
        if key != 'peak_frequency' and not (0 <= value <= upper_bound):
            raise ValueError(f"Metric '{key}' must be 0-{upper_bound}, got {value}")
        if key == 'peak_frequency' and value < 0:
            raise ValueError(f"Metric '{key}' must be >= 0, got {value}")
        validated[key] = float(value)

    return validated


# Example usage
if __name__ == "__main__":
    # Example transcript
    example_transcript = """
    Q: Tell me about a time you had to handle a difficult situation at work.
    
    A: In my last role, we had a production outage that affected 20% of our users. 
    I immediately gathered the team, we identified the issue was in our database 
    connection pool, implemented a fix, and had it deployed within 3 hours. 
    After that, I led a post-mortem to prevent similar issues.
    """
    
    # Example metrics (from your analysis phases)
    example_metrics = {
        'eye_contact': 78.5,
        'eye_contact_grade': 'Good',
        'posture': 72.3,
        'posture_grade': 'Good',
        'expressiveness': 57.8,
        'consistency': 76.6,
        'stability': 90.5,
        'animation_grade': 'Good - Well Animated',
        'peak_frequency': 0.33
    }
    
    try:
        # Validate metrics
        validated_metrics = validate_metrics(example_metrics)
        
        # Build prompt
        prompt = build_feedback_prompt(example_transcript, validated_metrics)
        
        print("="*60)
        print("GENERATED PROMPT:")
        print("="*60)
        print(prompt)
        print("="*60)
        
    except ValueError as e:
        print(f"Validation error: {e}")
