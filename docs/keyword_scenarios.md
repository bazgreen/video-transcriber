# Keyword Scenarios Feature Documentation

## Overview

The Keyword Scenarios feature allows users to quickly select pre-defined sets of keywords based on the type of content they are transcribing. Instead of manually configuring keywords for each type of video, users can now select from a variety of scenarios (like Education, Business, Interviews, etc.) to automatically apply the most relevant keywords.

## Benefits

- **Time-saving**: No need to manually configure keywords for each transcription
- **Consistent analysis**: Apply the same set of keywords across similar content types
- **Domain expertise**: Scenarios include domain-specific keywords designed for particular content
- **Customizable**: Apply scenarios as-is or merge them with your custom keywords

## Available Scenarios

1. **🎓 Education & Training**
   - Focused on learning environments
   - Keywords include: question, answer, explain, understand, learn, study, etc.

2. **💼 Business & Meetings**
   - Optimized for corporate environments
   - Keywords include: action item, deadline, follow up, next steps, decision, etc.

3. **🎤 Interviews & Research**
   - Designed for interview analysis
   - Keywords include: experience, background, opinion, perspective, challenge, etc.

4. **🔬 Technical & Development**
   - For technical discussions and presentations
   - Keywords include: bug, error, feature, requirement, test, deploy, etc.

## How to Use

### From the Web Interface

1. Navigate to the Upload page
2. Select your video file
3. Enter a session name
4. From the "Keyword Scenario" dropdown, select the scenario that best matches your content
5. Click "Process Video"

Your video will be transcribed with the selected scenario's keywords automatically applied for analysis.

### From the API

You can also use the keyword scenarios through our API:

#### List Available Scenarios

```http
GET /api/keywords/scenarios
```

#### Get Details for a Specific Scenario

```http
GET /api/keywords/scenarios/{scenario_id}
```

#### Apply a Scenario to Current Keywords

```json
POST /api/keywords/scenarios/apply
{
  "scenario_id": "education",
  "merge_mode": "replace" // or "merge"
}
```

## Creating Custom Scenarios

Currently, scenarios are managed by the system administrator. If you need a custom scenario for your specific use case, please contact the administrator to have it added to the system.

## Technical Implementation

The Keyword Scenarios feature is implemented across several components:

1. **Storage**: Scenarios are stored in `data/config/keyword_scenarios.json`
2. **Backend**: Scenarios are managed by utilities in `src/utils/keywords.py`
3. **API**: Endpoints for working with scenarios are available in `src/routes/api.py`
4. **UI**: Scenario selection is integrated into the upload form in `data/templates/index.html`
5. **Processing**: The transcription service in `src/services/transcription.py` applies the selected scenario during analysis

## Advanced Usage

### Merging Scenarios with Custom Keywords

When applying a scenario through the API, you can choose to either replace your current keywords or merge the scenario keywords with your existing ones:

- **Replace mode**: Completely replaces your current keywords with the scenario keywords
- **Merge mode**: Combines the scenario keywords with your existing custom keywords

### Fallback Mechanism

If a selected scenario is not found or contains no keywords, the system will automatically fall back to using your custom keywords from `keywords_config.json`.

## Performance Considerations

Keyword scenarios have minimal performance impact as they simply replace the source of keywords used during analysis. The number of keywords in a scenario may affect analysis time slightly, but this impact is typically negligible.
