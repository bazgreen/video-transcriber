# Add Education Dictionary to Transcript Correction System

## Issue Summary
Currently, the transcript correction system includes industry-specific dictionaries for medical, legal, technical, and business domains. We need to add an **education dictionary** to better support transcription correction for academic content, lectures, educational videos, and research discussions.

## Current Implementation
The industry dictionaries are defined in `src/services/transcript_correction.py` in the `INDUSTRY_DICTIONARIES` constant:

```python
INDUSTRY_DICTIONARIES = {
    'medical': { ... },
    'legal': { ... },
    'technical': { ... },
    'business': { ... }
}
```

## Proposed Solution
Add a comprehensive education dictionary that includes:

### Core Educational Terms
- **Academic Levels**: undergraduate, graduate, postgraduate, doctorate, PhD, Masters, Bachelors
- **Educational Roles**: professor, lecturer, instructor, teaching assistant, dean, provost
- **Academic Processes**: dissertation, thesis, curriculum, syllabus, pedagogy, assessment
- **Educational Institutions**: university, college, academy, institute, school, campus

### Subject-Specific Terms
- **Research**: methodology, hypothesis, literature review, peer review, empirical, qualitative, quantitative
- **Mathematics**: algebra, calculus, geometry, statistics, probability, theorem, equation
- **Science**: biology, chemistry, physics, laboratory, experiment, hypothesis, theory
- **Liberal Arts**: humanities, philosophy, linguistics, literature, sociology, psychology

### Academic Formats
- **Publications**: journal, publication, citation, bibliography, reference, abstract
- **Presentations**: symposium, conference, seminar, workshop, colloquium, lecture
- **Assessment**: examination, quiz, assignment, rubric, grading, evaluation

## Implementation Plan

### Phase 1: Dictionary Creation
1. Create comprehensive education dictionary with 100+ terms
2. Include proper capitalizations and common variations
3. Add subject-specific terminology for major academic disciplines

### Phase 2: Integration
1. Add education dictionary to `INDUSTRY_DICTIONARIES`
2. Ensure API endpoints recognize the new dictionary
3. Update frontend to display education as an option

### Phase 3: Enhancement
1. Add subject-specific sub-dictionaries (mathematics, science, literature, etc.)
2. Implement dynamic dictionary loading for educational content
3. Add learning capabilities for academic terminology

## Benefits
- **Improved Accuracy**: Better transcription correction for educational content
- **Academic Support**: Enhanced support for lecture transcriptions and research interviews
- **Subject Recognition**: Automatic recognition of academic terminology and proper nouns
- **User Experience**: More relevant suggestions for educational professionals

## Technical Requirements
- Maintain backward compatibility with existing dictionaries
- Ensure proper integration with correction engine
- Add comprehensive test coverage for education dictionary
- Update documentation and API endpoints

## Success Metrics
- Education dictionary contains 100+ relevant terms
- Integration tests pass for all new terms
- API correctly returns education dictionary
- Frontend properly displays education option
- Quality improvement measurable for educational content

## Related Files
- `src/services/transcript_correction.py` - Main dictionary definitions
- `src/routes/transcript_correction_routes.py` - API endpoints
- `data/templates/transcript-correction.html` - Frontend interface
- `data/static/js/transcript-correction.js` - Frontend logic

## Priority
**Medium** - This feature enhances the system's utility for educational institutions and academic professionals, expanding the target user base and improving transcription quality for educational content.

---

**Labels**: enhancement, feature, education, dictionary, transcript-correction
**Assignee**: @bazgreen
**Milestone**: v1.2.0 - Educational Features
