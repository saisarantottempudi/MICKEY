import subprocess


def get_today_events() -> str:
    script = '''
    tell application "Calendar"
        set today to current date
        set time of today to 0
        set tomorrow to today + (1 * days)
        set output to ""
        repeat with cal in calendars
            try
                repeat with evt in (every event of cal whose start date >= today and start date < tomorrow)
                    set output to output & summary of evt & " at " & time string of start date of evt & linefeed
                end repeat
            end try
        end repeat
        if output is "" then
            return "No events today."
        end if
        return output
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        return f"Could not access Calendar: {result.stderr.strip()}"
    return result.stdout.strip() or "No events today."
