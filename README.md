## What this is
A small Python automation script that uses nodriver to control Chrome and send connection requests on LinkedIn while enforcing daily/weekly caps and recording runs. It's intended for a single-user, desktop/browser-driven workflow that reuses a Chrome user profile and logs activity to AccountLog.txt.

### Stack
- **Language(s):** Python (single-file script)
- **Framework / runtime:** Plain Python script using asyncio (run with Python 3.9+)
- **Notable libraries:** nodriver (browser automation), asyncio (concurrency), logging (runtime logging)

## How it's organized
```
main.py           Single-file bot: configuration, skip-logic, browser automation, logging
requirements.txt  Dependency list (nodriver)
```

How it fits together: main.py contains the entire runtime. On start it parses AccountLog.txt (LOG_FILE) to decide whether to skip today's run based on MAX_DAILY_CONNECTS and MAX_WEEKLY_ACCOUNTS, then launches a browser via nodriver, navigates to LinkedIn's "My Network" grow page, finds invite/connect UI elements, sends connection requests up to the daily cap, and appends a run record to the log when successful. Key functions you can inspect are parse_log_file, should_skip, run_bot, and append_log.

## How to run it
1. Install dependencies:
   ```
   python -m pip install -r requirements.txt
   ```
2. Edit configuration at the top of main.py:
   - BROWSER_PATH: path to your Chrome executable
   - PROFILE_PATH: path to a Chrome user profile directory to reuse cookies/login
   - LOGGED_IN: set to False if you want to log in manually when the browser opens
   - MAX_WEEKLY_ACCOUNTS, MAX_DAILY_CONNECTS, LOOKBACK_DAYS: adjust limits
3. Run the bot:
   ```
   python main.py
   ```
Notes and requirements:
- The script expects a Windows-style Chrome path by default (change BROWSER_PATH/PROFILE_PATH for your OS).
- The code uses nodriver to start and control the browser; ensure Chrome is installed and compatible with the nodriver version.
- Python 3.9+ is recommended (uses builtin generic types like list[dict]).
- The log file used is AccountLog.txt (created if missing). Each appended line format used by the script is:
  ```
  Accounts ran: <count> on YYYY-MM-DD
  ```

## Try asking
- Where in main.py should I change BROWSER_PATH and PROFILE_PATH to run this on macOS or Linux?
- main.py references LOG_FILE = "AccountLog.txt" — what happens if that file is missing or malformed lines are present?
- Could the nodriver usage in run_bot be adapted to run headless, and which browser_args would you change in main.py to do that?
