# 🐛 Issue: Browser Opens Before App is Ready

## Problem Description
The setup script (`scripts/setup/setup_and_run.py`) opens the browser too early, before the Flask application has fully started and is ready to serve requests. This results in:

- Browser showing "connection refused" or loading errors
- Poor user experience during initial setup
- Users thinking the installation failed

## Current Behavior
1. Setup script starts Flask app in background
2. Browser opens immediately (2-second delay)
3. Flask app may still be initializing
4. User sees error page instead of working application

## Expected Behavior
1. Setup script starts Flask app
2. Script waits for app to be fully ready and responsive
3. Browser opens only after app confirms it's serving requests
4. User sees working application immediately

## Technical Details
- Location: `scripts/setup/setup_and_run.py`
- Function: `open_browser_delayed()` and `run_app()`
- Current delay: 2 seconds (hardcoded)
- Flask startup time varies based on system performance

## Proposed Solution
Replace fixed 2-second delay with intelligent health check:

1. **Health Check Endpoint**: Add `/health` endpoint to Flask app
2. **Polling Mechanism**: Script polls health endpoint until ready
3. **Timeout Protection**: Maximum wait time to prevent infinite loops
4. **User Feedback**: Show progress messages during startup

## Success Criteria
- [ ] Browser opens only when app is fully ready
- [ ] No more "connection refused" errors during setup
- [ ] Improved user experience during installation
- [ ] Robust timeout handling for edge cases

## Priority
**High** - Affects first-time user experience and setup reliability

## Labels
- `bug`
- `user-experience` 
- `installation`
- `high-priority`
