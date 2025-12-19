import os
import json
import base64
import re
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

JIRA_BASE_URL = os.environ["JIRA_BASE_URL"].rstrip("/")
JIRA_EMAIL = os.environ["JIRA_EMAIL"]
JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]  # RAW token
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "IIS")
JIRA_ISSUE_TYPE = os.getenv("JIRA_ISSUE_TYPE", "Task")

# Detect IIS-123 style keys anywhere in text
ISSUE_KEY_RE = re.compile(r"\bIIS-\d+\b", re.IGNORECASE)


# -----------------------------
# Bedrock response helpers
# -----------------------------
def bedrock_response(event: Dict[str, Any], status: int, body_obj: Dict[str, Any]) -> Dict[str, Any]:
    # Bedrock expects these keys to correlate the API execution
    action_group = event.get("actionGroup")
    api_path = event.get("apiPath")
    http_method = event.get("httpMethod")

    # If missing, return a usable error that shows keys
    if not action_group or not api_path or not http_method:
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": action_group or "UNKNOWN",
                "apiPath": api_path or "/UNKNOWN",
                "httpMethod": http_method or "POST",
                "httpStatusCode": 500,
                "responseBody": {
                    "application/json": {
                        "body": json.dumps({
                            "error": "Missing required Bedrock routing keys in event",
                            "missing": [k for k in ["actionGroup", "apiPath", "httpMethod"] if not event.get(k)],
                            "eventKeys": list(event.keys())
                        })
                    }
                },
            },
        }

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group,
            "apiPath": api_path,
            "httpMethod": http_method,
            "httpStatusCode": int(status),
            "responseBody": {
                "application/json": {
                    "body": json.dumps(body_obj)
                }
            },
        },
        "sessionAttributes": event.get("sessionAttributes", {}) or {},
        "promptSessionAttributes": event.get("promptSessionAttributes", {}) or {},
    }


# -----------------------------
# Bedrock event parsing
# -----------------------------
def params_to_dict(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Supports Bedrock Agents action-group payload styles:
    - parameters: [{"name":"x","value":"y"}]
    - requestBody.content.application/json: either { ... } or {"properties":[{"name","value"}]}
    """
    out: Dict[str, Any] = {}

    for p in event.get("parameters", []) or []:
        n = p.get("name")
        v = p.get("value")
        if n:
            out[n] = v

    rb = event.get("requestBody") or {}
    content = (rb.get("content") or {})
    app_json = content.get("application/json")

    if isinstance(app_json, dict):
        props = app_json.get("properties")
        if isinstance(props, list):
            for prop in props:
                n = prop.get("name")
                v = prop.get("value")
                if n:
                    out[n] = v
        else:
            # Sometimes Bedrock passes the JSON object directly
            for k, v in app_json.items():
                if k not in out:
                    out[k] = v

    # Some setups pass "body" as a JSON string
    if isinstance(event.get("body"), str):
        try:
            body_obj = json.loads(event["body"])
            if isinstance(body_obj, dict):
                out.update({k: v for k, v in body_obj.items() if k not in out})
        except Exception:
            pass

    return out


def pick_first(params: Dict[str, Any], keys) -> Optional[str]:
    for k in keys:
        v = params.get(k)
        if v is not None and str(v).strip():
            return str(v)
    return None


def find_issue_key(*texts: Optional[str]) -> Optional[str]:
    for t in texts:
        if not t:
            continue
        m = ISSUE_KEY_RE.search(t)
        if m:
            return m.group(0).upper()
    return None


# -----------------------------
# Jira helpers
# -----------------------------
def adf_text_doc(text: str) -> Dict[str, Any]:
    # Atlassian Document Format (ADF) for Jira Cloud description (API v3)
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": text or ""}]}
        ],
    }


def jira_request(method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{JIRA_BASE_URL}{path}"

    userpass = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode("utf-8")
    auth_header = base64.b64encode(userpass).decode("utf-8")

    data = None
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Accept": "application/json",
    }

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url=url, data=data, method=method.upper(), headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            return {"status": resp.status, "body": json.loads(body) if body else {}}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "error": "Jira HTTPError", "body": e.read().decode("utf-8", errors="replace")}
    except urllib.error.URLError as e:
        return {"status": 500, "error": "Jira URLError", "body": str(e)}


def create_task(summary: str, description: str) -> Dict[str, Any]:
    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "issuetype": {"name": JIRA_ISSUE_TYPE},  # usually "Task"
            "summary": summary,
            "description": adf_text_doc(description),
        }
    }
    return jira_request("POST", "/rest/api/3/issue", payload)


def get_issue(issue_key: str) -> Dict[str, Any]:
    return jira_request("GET", f"/rest/api/3/issue/{issue_key}")


def compact_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    fields = issue.get("fields", {}) or {}
    key = issue.get("key")
    return {
        "key": key,
        "summary": fields.get("summary"),
        "status": (fields.get("status") or {}).get("name"),
        "priority": (fields.get("priority") or {}).get("name"),
        "assignee": (fields.get("assignee") or {}).get("displayName"),
        "reporter": (fields.get("reporter") or {}).get("displayName"),
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "browseUrl": f"{JIRA_BASE_URL}/browse/{key}" if key else None,
    }


# -----------------------------
# Main handler
# -----------------------------
def lambda_handler(event, context):
    params = params_to_dict(event)

    # We support two patterns:
    # A) Create ticket -> provide summary + description
    # B) Fetch ticket -> provide issueKey OR mention IIS-123 in any text field

    summary = pick_first(params, ["summary", "name", "title"])
    description = pick_first(params, ["description", "details", "body", "text"])
    issue_key = pick_first(params, ["issueKey", "ticketKey", "key"])

    # If no explicit issueKey, try to detect IIS-### anywhere
    detected_key = find_issue_key(issue_key, summary, description)
    if detected_key:
        jira_res = get_issue(detected_key)
        if jira_res.get("status") == 200:
            return bedrock_response(event, 200, {"mode": "fetch", "ticket": compact_issue(jira_res.get("body", {}))})
        return bedrock_response(event, int(jira_res.get("status", 500)), {"mode": "fetch", "error": "Failed to fetch ticket", "jira": jira_res})

    # Otherwise, create a ticket
    if not summary or not description:
        return bedrock_response(
            event,
            400,
            {
                "error": "Provide either an IIS-### ticket key (to fetch) or summary+description (to create).",
                "received": params
            },
        )

    jira_res = create_task(summary, description)
    if jira_res.get("status") in (200, 201):
        created = jira_res.get("body", {})
        key = created.get("key")
        return bedrock_response(
            event,
            200,
            {
                "mode": "create",
                "result": "created",
                "key": key,
                "browseUrl": f"{JIRA_BASE_URL}/browse/{key}" if key else None,
                "jira": created,
            },
        )

    return bedrock_response(
        event,
        int(jira_res.get("status", 500)),
        {"mode": "create", "error": "Failed to create Jira Task", "jira": jira_res},
    )
