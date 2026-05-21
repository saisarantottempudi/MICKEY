import json
from system_commands import apps, filesystem, calendar_cmd, system_info

COMMAND_MAP = {
    "open_app": apps.open_app,
    "close_app": apps.close_app,
    "read_file": filesystem.read_file,
    "list_dir": filesystem.list_directory,
    "calendar_today": calendar_cmd.get_today_events,
    "system_info": system_info.get_info,
}


def route(llm_response: str) -> dict:
    cleaned = llm_response.strip()
    # Try to extract JSON from the response (model sometimes wraps in markdown)
    if "```" in cleaned:
        for block in cleaned.split("```"):
            block = block.strip()
            if block.startswith("json"):
                block = block[4:].strip()
            try:
                parsed = json.loads(block)
                if "action" in parsed:
                    return _execute(parsed)
            except (json.JSONDecodeError, ValueError):
                continue

    try:
        parsed = json.loads(cleaned)
        if "action" in parsed:
            return _execute(parsed)
    except (json.JSONDecodeError, ValueError):
        pass

    return {"type": "conversation", "result": llm_response}


def _execute(parsed: dict) -> dict:
    action = parsed.get("action")
    params = parsed.get("params", {})
    handler = COMMAND_MAP.get(action)
    if handler:
        try:
            result = handler(**params)
            return {"type": "action_result", "action": action, "result": result}
        except Exception as e:
            return {"type": "error", "action": action, "result": str(e)}
    return {"type": "error", "result": f"Unknown action: {action}"}
