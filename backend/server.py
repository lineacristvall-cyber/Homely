"""Dependency-light same-origin server for the local Homely POC.

Run from the repository root: python3 -m backend.server
The HTTP service binds to loopback only. Secrets remain in ignored .env.local.
"""
from __future__ import annotations

import base64
import copy
import json
import mimetypes
import math
import secrets
import contextvars
import time
from http.cookies import SimpleCookie
import os
import re
import threading
import traceback
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image
from backend.assistant import AssistantError
from backend.cloud import CloudSettings, CloudError
from backend.cloud.session_auth import AuthManager, AuthError
from backend.cloud.project_store import CloudProjectStore

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
DATA = ROOT / "data"
PROJECTS = DATA / "projects"
ASSETS = DATA / "assets"
JOBS = DATA / "jobs"
LOCK = threading.RLock()
MAX_JSON = 18 * 1024 * 1024
MAX_IMAGE = 12 * 1024 * 1024
PENDING_ACTIONS = {}
CONFIRM_TTL = 300
CURRENT_CLOUD = contextvars.ContextVar("homely_cloud", default=None)
CURRENT_OWNER = contextvars.ContextVar("homely_owner", default=None)
AUTH_MANAGER = None
PRICE_WATCH_STORE = None


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def setting(name, default=None):
    if name in os.environ:
        return os.environ[name]
    path = ROOT / ".env.local"
    if path.exists():
        for line in path.read_text().splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    return default


def api_key():
    return setting("OPENAI_API_KEY")


def cloud_enabled():
    return setting("HOMELY_STORAGE", "local") == "cloud"


def auth_manager():
    global AUTH_MANAGER
    with LOCK:
        if AUTH_MANAGER is None:
            AUTH_MANAGER = AuthManager(CloudSettings(publishable_key=setting("SUPABASE_PUBLISHABLE_KEY", "")))
        return AUTH_MANAGER


def price_watch_store():
    global PRICE_WATCH_STORE
    from backend.price_watch import PriceWatchStore
    with LOCK:
        target = DATA / "private-price-watches.json"
        if PRICE_WATCH_STORE is None or PRICE_WATCH_STORE.path != target:
            if PRICE_WATCH_STORE is not None:
                PRICE_WATCH_STORE.stop()
            PRICE_WATCH_STORE = PriceWatchStore(target)
            PRICE_WATCH_STORE.start()
        return PRICE_WATCH_STORE


def watch_owner():
    if cloud_enabled():
        owner = CURRENT_OWNER.get()
        if not owner:
            raise CloudError("Sign in to access your price watches.", 401)
        return owner
    return "local-preview"


def cloud_store():
    session = CURRENT_CLOUD.get()
    if session is None:
        raise CloudError("Sign in to access your cloud workspace.", 401)
    return CloudProjectStore(session)


def background(target, *args):
    context = contextvars.copy_context()
    threading.Thread(target=context.run, args=(target, *args), daemon=True).start()


def job_directory():
    return DATA / "private-cloud-jobs" if cloud_enabled() else JOBS


def asset_directory():
    return DATA / "private-cloud-cache" if cloud_enabled() else ASSETS


def ensure_dirs():
    for folder in (PROJECTS, ASSETS, JOBS, job_directory(), asset_directory()):
        folder.mkdir(parents=True, exist_ok=True)


def _atomic_json(path, obj):
    ensure_dirs()
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(obj, indent=2, ensure_ascii=False))
    os.replace(temporary, path)


def get_project(project_id):
    if cloud_enabled():
        return cloud_store().get(project_id)
    if not re.fullmatch(r"[a-f0-9-]{36}", project_id):
        return None
    path = PROJECTS / (project_id + ".json")
    if not path.exists():
        return None
    with LOCK:
        return json.loads(path.read_text())


def save_project(project):
    if cloud_enabled():
        store = cloud_store()
        result = store.create(project) if project.get("version") == 1 else store.save(project)
        project.clear()
        project.update(result)
        return
    with LOCK:
        _atomic_json(PROJECTS / (project["id"] + ".json"), project)


def list_projects():
    if cloud_enabled():
        return cloud_store().list()
    ensure_dirs()
    with LOCK:
        result = [json.loads(p.read_text()) for p in PROJECTS.glob("*.json")]
    return sorted(result, key=lambda p: p["createdAt"], reverse=True)


def get_job(job_id):
    if not re.fullmatch(r"[a-f0-9-]{36}", job_id):
        return None
    path = job_directory() / (job_id + ".json")
    if not path.exists():
        return None
    with LOCK:
        job = json.loads(path.read_text())
        if cloud_enabled() and (not CURRENT_OWNER.get() or job.get("ownerId") != CURRENT_OWNER.get()):
            return None
        return job



def served_job(job, project=None):
    """Apply the same historical-render freshness rule to every read surface."""
    if not job:
        return job
    job = copy.deepcopy(job)
    if job.get("kind") == "visualization" and job.get("status") == "completed":
        project = project if project is not None else get_project(job.get("projectId", ""))
        if not project or project["version"] != job.get("projectVersion"):
            job["status"] = "cancelled"
            job["progress"] = "This render belongs to an earlier project version."
            if isinstance(job.get("result"), dict):
                job["result"]["stale"] = True
    return job


def visualization_history(project):
    """Read recent jobs from this mode's directory after project authorization."""
    jobs = []
    for path in job_directory().glob("*.json"):
        if not re.fullmatch(r"[a-f0-9-]{36}", path.stem):
            continue
        try:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_JSON:
                continue
            job = get_job(path.stem)
            if (not isinstance(job, dict) or job.get("id") != path.stem
                    or job.get("projectId") != project["id"] or job.get("kind") != "visualization"
                    or job.get("status") not in ("queued", "running", "completed", "failed", "cancelled")
                    or (not cloud_enabled() and job.get("ownerId") is not None)):
                continue
            if job.get("result") is not None and not isinstance(job["result"], dict):
                continue
            stamp = datetime.fromisoformat(job["createdAt"].replace("Z", "+00:00"))
            if stamp.tzinfo is None or stamp.utcoffset() is None:
                continue
            jobs.append((stamp.astimezone(timezone.utc), job["id"], job))
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            # Corrupt, incomplete or concurrently removed files are not history.
            continue
    jobs.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
    return [served_job(job, project) for _, _, job in jobs[:50]]


def save_job(job):
    with LOCK:
        _atomic_json(job_directory() / (job["id"] + ".json"), job)


def new_job(project_id, kind):
    job = {
        "id": str(uuid.uuid4()),
        "projectId": project_id,
        "ownerId": CURRENT_OWNER.get(),
        "kind": kind,
        "status": "queued",
        "progress": "Waiting to start",
        "error": None,
        "result": None,
        "createdAt": now_iso(),
        "updatedAt": now_iso(),
    }
    save_job(job)
    return job


def update_job(job_id, **changes):
    with LOCK:
        job = get_job(job_id)
        if job is None:
            return
        if job.get("status") == "cancelled" and changes.get("status") not in (None, "cancelled"):
            return
        job.update(changes)
        job["updatedAt"] = now_iso()
        save_job(job)


def decode_image(data_url):
    match = re.fullmatch(r"data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)", data_url or "")
    if not match:
        raise ValueError("Upload a PNG, JPEG, or WebP image.")
    try:
        raw = base64.b64decode(match.group(2), validate=True)
    except Exception:
        raise ValueError("Image data is invalid.")
    if not raw or len(raw) > MAX_IMAGE:
        raise ValueError("Image must be under 12 MB.")
    try:
        image = Image.open(BytesIO(raw))
        image.verify()
    except Exception:
        raise ValueError("Image could not be decoded.")
    return raw, {"png": ".png", "jpeg": ".jpg", "webp": ".webp"}[match.group(1)]


def save_asset(data_url, project_id=None, kind="room_original", consent=True):
    raw, extension = decode_image(data_url)
    ensure_dirs()
    asset_id = str(uuid.uuid4()) + extension
    path = asset_directory() / asset_id
    path.write_bytes(raw)
    if cloud_enabled():
        meta = cloud_store().upload(project_id, kind, raw, mimetypes.guess_type(asset_id)[0], {"upload": consent is True})
        return path, meta["imageUrl"]
    return path, "/api/assets/" + asset_id


def delivered_total(candidate, quantity):
    try:
        item = float(candidate["unitPrice"]) * int(quantity)
        shipping = candidate.get("shipping")
        tax = candidate.get("tax")
        if shipping is None or tax is None:
            return None
        return round(item + float(shipping) + float(tax), 2)
    except (KeyError, TypeError, ValueError):
        return None


def research_worker(job_id, project_id, project_version):
    if (get_job(job_id) or {}).get("status") == "cancelled":
        return
    update_job(job_id, status="running", progress="Searching supported public sources")
    try:
        from backend.sourcing import search_products_with_coverage, SourcingError, verify_candidate
        project = get_project(project_id)
        if project is None:
            raise ValueError("Project no longer exists.")
        results = search_products_with_coverage(copy.deepcopy(project["brief"]), api_key())
        checked = [verify_candidate(c, project["brief"]) for c in results["candidates"]]
        coverage = copy.deepcopy(results["coverage"])
        with LOCK:
            current = get_project(project_id)
            if (get_job(job_id) or {}).get("status") == "cancelled":
                return
            if current is None or current["version"] != project_version:
                update_job(job_id, status="cancelled", progress="Brief changed; old search was discarded")
                return
            current["candidates"] = checked
            current["sourceCoverage"] = coverage
            current["sourceCoverageComplete"] = False
            current["version"] += 1
            current["updatedAt"] = now_iso()
            save_project(current)
        update_job(job_id, status="completed", progress="Research complete", result={"candidateCount": len(checked), "projectVersion": current["version"], "sourceCoverage": coverage, "sourceCoverageComplete": False})
    except SourcingError as exc:
        with LOCK:
            current = get_project(project_id)
            if (get_job(job_id) or {}).get("status") == "cancelled":
                return
            if current is None or current["version"] != project_version:
                update_job(job_id, status="cancelled", progress="Brief changed; old search was discarded")
                return
            update_job(job_id, status="failed", progress="Research could not complete", error=str(exc)[:500],
                       result={"sourceCoverage": copy.deepcopy(exc.coverage), "sourceCoverageComplete": False})
    except Exception as exc:
        update_job(job_id, status="failed", progress="Research could not complete", error=str(exc)[:500])


def visualization_worker(job_id, project_id, candidate_id, product_path, output_path, rights_confirmed, product_url=None, project_snapshot=None):
    if (get_job(job_id) or {}).get("status") == "cancelled":
        return
    update_job(job_id, status="running", progress="Preparing original room and product references")
    try:
        from backend.visualization import create_visualization
        project = copy.deepcopy(project_snapshot) if project_snapshot is not None else get_project(project_id)
        if project is None:
            raise ValueError("Project no longer exists.")
        current = get_project(project_id)
        if current is None or current["version"] != project["version"]:
            update_job(job_id, status="cancelled", progress="Project changed before rendering; review and try again")
            return
        room = project.get("room") or {}
        room_name = Path(urlparse(room.get("imageUrl", "")).path).name
        room_path = ASSETS / room_name
        if cloud_enabled():
            if not str(room.get("imageUrl", "")).startswith("/api/cloud-assets/"):
                raise ValueError("Upload the room photo to this cloud project first.")
            room_bytes, room_mime = cloud_store().read(room_name)
            room_path = asset_directory() / (str(uuid.uuid4()) + (mimetypes.guess_extension(room_mime) or ".png"))
            room_path.write_bytes(room_bytes)
        candidate = next((c for c in project.get("candidates", []) if c["id"] == candidate_id), None)
        if candidate is None:
            raise ValueError("Candidate no longer exists.")
        brief = copy.deepcopy(project["brief"])
        brief["roomConsent"] = bool(room.get("consent"))
        brief["roomImageUrl"] = room.get("imageUrl")
        candidate = copy.deepcopy(candidate)
        candidate["productImageRightsConfirmed"] = rights_confirmed
        candidate["merchantImageUrl"] = candidate.get("imageUrl")
        candidate["sourceImageUrl"] = product_url or "/api/assets/" + product_path.name
        result = create_visualization(room_path, product_path, candidate, brief, api_key(), output_path)
        result["projectVersion"] = project["version"]
        result["briefSnapshot"] = copy.deepcopy(project["brief"])
        current = get_project(project_id)
        if (get_job(job_id) or {}).get("status") == "cancelled" or current is None or current["version"] != project["version"]:
            result["stale"] = True
            update_job(job_id, status="cancelled", progress="Project changed or render cancelled; output is not current", result=result)
            return
        if result.get("status") == "generated" and output_path.exists():
            if cloud_enabled():
                meta = cloud_store().upload(project_id, "illustrative_render", output_path.read_bytes(), "image/png", {"upload": True}, lineage=result)
                result["imageUrl"] = meta["imageUrl"]
            else:
                result["imageUrl"] = "/api/assets/" + output_path.name
        with LOCK:
            current = get_project(project_id)
            if (get_job(job_id) or {}).get("status") == "cancelled" or current is None or current["version"] != project["version"]:
                result["stale"] = True
                update_job(job_id, status="cancelled", progress="Project changed or render cancelled; output is not current", result=result)
                return
            update_job(job_id, status="completed" if result.get("status") == "generated" else "failed", progress="Visualization finished" if result.get("status") == "generated" else "Visualization unavailable", result=result, error=None if result.get("status") == "generated" else result.get("reason"))
    except Exception as exc:
        update_job(job_id, status="failed", progress="Visualization could not complete", error=str(exc)[:500])


class ConflictError(ValueError):
    pass


def validate_brief(previous, patch):
    if not isinstance(patch, dict):
        raise ValueError("Brief is required.")
    allowed = ("itemType", "quantity", "style", "location", "flexibleTarget", "hardCap", "notes", "measurements", "roomType", "roomLabel", "furnishingMode", "retainedItems", "journey", "fit")
    if set(patch) - set(allowed):
        raise ValueError("Brief contains unsupported fields.")
    clean = {**previous, **patch}
    if "journey" in clean:
        from backend.journey import validate_journey
        clean["journey"] = validate_journey(clean["journey"])
    if "fit" in clean:
        from backend.fit import validate_fit_config
        clean["fit"] = validate_fit_config(clean["fit"])
    if clean.get("roomType") not in (None, "dining", "living", "bedroom", "other"):
        raise ValueError("Choose a supported room type.")
    if clean.get("furnishingMode") not in (None, "keep", "from_scratch"):
        raise ValueError("Choose whether to keep furniture or furnish from scratch.")
    if "roomLabel" in clean:
        label = clean["roomLabel"]
        if not isinstance(label, str) or len(label.strip()) > 100:
            raise ValueError("Room name must be text of at most 100 characters.")
        clean["roomLabel"] = label.strip()
    if "retainedItems" in clean:
        items = clean["retainedItems"]
        if not isinstance(items, list) or len(items) > 20 or any(
            not isinstance(item, str) or not item.strip() or len(item.strip()) > 100
            for item in items
        ):
            raise ValueError("Keep up to 20 named pieces, each at most 100 characters.")
        clean["retainedItems"] = list(dict.fromkeys(item.strip() for item in items))
    quantity = clean.get("quantity")
    if isinstance(quantity, bool):
        raise ValueError("Quantity must be between 1 and 100.")
    try:
        q = float(quantity)
    except (TypeError, ValueError):
        raise ValueError("Quantity must be between 1 and 100.")
    if not math.isfinite(q) or not q.is_integer() or not 1 <= q <= 100:
        raise ValueError("Quantity must be between 1 and 100.")
    clean["quantity"] = int(q)
    for key in ("flexibleTarget", "hardCap"):
        value = clean.get(key)
        if value in (None, ""):
            clean[key] = None
        else:
            if isinstance(value, bool):
                raise ValueError("Budgets must be finite non-negative amounts.")
            try:
                value = float(value)
            except (TypeError, ValueError):
                raise ValueError("Budgets must be finite non-negative amounts.")
            if not math.isfinite(value) or value < 0:
                raise ValueError("Budgets must be finite non-negative amounts.")
            clean[key] = value
    if clean["flexibleTarget"] is not None and clean["hardCap"] is not None and clean["flexibleTarget"] > clean["hardCap"]:
        raise ValueError("Flexible target cannot exceed the hard cap.")
    for key, limit in (("itemType",100),("style",250),("location",150),("notes",2000)):
        value = clean.get(key, "")
        if not isinstance(value, str):
            raise ValueError("Brief text fields must contain text.")
        clean[key] = value.strip()[:limit]
    if not clean["itemType"]:
        raise ValueError("Item type is required.")
    measurements = clean.get("measurements", {})
    if not isinstance(measurements, dict):
        raise ValueError("Measurements must be an object.")
    merged = dict(previous.get("measurements") or {})
    for key, value in measurements.items():
        if key not in ("tableUndersideIn", "chairArmIn", "roomWidthIn", "roomDepthIn"):
            raise ValueError("Unsupported measurement.")
        if value in (None, ""):
            merged[key] = None
            continue
        if isinstance(value, bool):
            raise ValueError("Measurements must be positive finite inches.")
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise ValueError("Measurements must be positive finite inches.")
        if not math.isfinite(value) or value <= 0:
            raise ValueError("Measurements must be positive finite inches.")
        merged[key] = value
    clean["measurements"] = merged
    return clean


def current_version(project_id, expected_version):
    project = get_project(project_id)
    if project is None:
        raise ValueError("Project not found.")
    if isinstance(expected_version, bool) or expected_version != project["version"]:
        raise ConflictError("Project changed. Reload and review the current brief before continuing.")
    return project


def patch_brief(project_id, expected_version, patch):
    with LOCK:
        project = current_version(project_id, expected_version)
        from backend.journey import validate_anchors
        previous = project["brief"]
        clean = validate_brief(previous, patch)
        validate_anchors(clean.get("journey"), project.get("room"))
        project["brief"] = clean
        # Step progress, geometry and fit evidence must not delete research.
        research_fields = {"itemType", "quantity", "style", "location", "flexibleTarget", "hardCap", "notes"}
        if any(previous.get(k) != clean.get(k) for k in research_fields):
            project["candidates"] = []
            project["sourceCoverage"] = []
            project["sourceCoverageComplete"] = False
        project["version"] += 1
        project["updatedAt"] = now_iso()
        save_project(project)
        return project


def record_decision(project_id, expected_version, candidate_id):
    with LOCK:
        project = current_version(project_id, expected_version)
        candidate = next((c for c in project["candidates"] if c["id"] == candidate_id), None)
        if candidate is None:
            raise ValueError("Select a candidate in the current project.")
        total = delivered_total(candidate, project["brief"]["quantity"])
        cap = project["brief"].get("hardCap")
        decision = {"id": str(uuid.uuid4()), "candidateId": candidate_id, "createdAt": now_iso(),
                    "projectVersion": project["version"], "deliveredTotal": total,
                    "withinHardCap": total is not None and cap is not None and total <= float(cap),
                    "status": "saved", "readyForHandoff": False,
                    "candidateSnapshot": copy.deepcopy(candidate), "briefSnapshot": copy.deepcopy(project["brief"])}
        project["decisions"].append(decision)
        project["version"] += 1
        project["updatedAt"] = now_iso()
        save_project(project)
        return decision, project


def start_research(project_id, expected_version, mode="fit"):
    with LOCK:
        project = current_version(project_id, expected_version)
        if mode not in ("fit", "inspiration"):
            raise ValueError("Choose fitting recommendations or inspiration.")
        if mode == "fit":
            from backend.fit import gate_requirements
            gate = gate_requirements(project["brief"])
            if gate["status"] != "passed":
                raise ValueError("Measurements are incomplete or conflicting. Complete the fit check or explicitly browse inspiration.")
        job = new_job(project_id, "research")
        job["resultMode"] = mode
        job["projectVersion"] = project["version"]
        save_job(job)
        background(research_worker, job["id"], project_id, project["version"])
        return job


def assistant_request(project_id, body, session_id):
    from backend.assistant import plan_message
    with LOCK:
        project = current_version(project_id, body.get("expectedVersion"))
        expired = [k for k, v in PENDING_ACTIONS.items() if time.monotonic() - v["at"] > CONFIRM_TTL]
        for key in expired:
            PENDING_ACTIONS.pop(key, None)
        confirmation_id = body.get("confirmationId")
        if confirmation_id:
            pending = PENDING_ACTIONS.get(confirmation_id)
            if not pending or pending["session"] != session_id or pending["projectId"] != project_id:
                raise ValueError("This confirmation is unavailable. Ask again to review a new proposal.")
            if pending["version"] != project["version"]:
                PENDING_ACTIONS.pop(confirmation_id, None)
                raise ConflictError("Project changed. Ask again to review a new proposal.")
            action = PENDING_ACTIONS.pop(confirmation_id)["action"]
            kind = action["type"]
            if kind == "update_brief":
                changed = patch_brief(project_id, project["version"], action["patch"])
                return {"reply": "Your brief is updated. Run research again for this brief.", "project": changed}
            if kind == "save_decision":
                decision, changed = record_decision(project_id, project["version"], action["candidateId"])
                return {"reply": "Saved to your decisions. Stock and delivered cost still require verification before handoff.", "project": changed, "decision": decision}
            if kind == "start_research":
                return {"reply": "Research is queued. Findings will show the evidence returned by the sources.", "job": start_research(project_id, project["version"])}
            raise ValueError("Unsupported proposed action.")
    # Network planning never holds the persistence lock. Recheck after it returns.
    proposal = plan_message(body.get("message"), copy.deepcopy(project), api_key())
    with LOCK:
        current = current_version(project_id, project["version"])
        action = proposal.get("action")
        if action is None:
            return {"reply": proposal["reply"]}
        kind = action.get("type")
        ids = {c["id"] for c in current["candidates"]}
        if kind in ("filter_candidates", "compare_candidates"):
            selected = action.get("candidateIds")
            if not isinstance(selected, list) or any(not isinstance(i,str) or i not in ids for i in selected):
                raise ValueError("Choose products from this project's current findings.")
            return {"reply": "Showing the selected findings." if kind == "filter_candidates" else "Opening those products for comparison.", "command": {"type": kind, "candidateIds": selected}}
        if kind in ("save_decision", "request_visualization") and action.get("candidateId") not in ids:
            raise ValueError("Choose a product from this project's current findings.")
        if kind == "request_visualization":
            return {"reply": "Open the visualization setup to provide the room and product references and confirm image use.", "command": {"type": kind, "candidateId": action["candidateId"]}}
        if kind == "update_brief":
            clean = validate_brief(current["brief"], action.get("patch"))
            action = {"type": kind, "patch": {k: clean[k] for k in action["patch"]}}
            summary = "Update your brief: " + "; ".join(k + " = " + json.dumps(v, ensure_ascii=False) for k, v in action["patch"].items()) + ". Current findings will be cleared for the revised brief."
        elif kind == "save_decision":
            candidate = next(c for c in current["candidates"] if c["id"] == action["candidateId"])
            summary = "Save " + str(candidate.get("title", "this product")) + " to your decisions? This does not verify stock or purchase it."
        elif kind == "start_research":
            summary = "Run live research using your saved brief? This sends the brief to the research provider."
        else:
            raise ValueError("This assistant action is not supported.")
        # Only the most recent proposal for a browser/project can be confirmed.
        for key in [k for k,v in PENDING_ACTIONS.items() if v["session"] == session_id and v["projectId"] == project_id]:
            PENDING_ACTIONS.pop(key, None)
        token = secrets.token_urlsafe(24)
        PENDING_ACTIONS[token] = {"session": session_id, "projectId": project_id, "version": current["version"], "action": action, "at": time.monotonic()}
        return {"reply": "Review this proposed action before it runs.", "confirmation": {"id": token, "summary": summary, "expectedVersion": current["version"]}}


class Handler(BaseHTTPRequestHandler):
    server_version = "HomelyPOC/0.1"

    def log_message(self, format_string, *args):
        # Deliberately omit request paths and bodies: they may contain private assets.
        return

    def _auth_cookie(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
            return cookie["homely_auth"].value if "homely_auth" in cookie else None
        except Exception:
            return None

    def _dispatch(self, handler):
        cloud_token = CURRENT_CLOUD.set(None)
        owner_token = CURRENT_OWNER.set(None)
        try:
            if not self._request_origin_allowed():
                return
            path = urlparse(self.path).path
            public_api = path in ("/api/health", "/api/progress", "/api/capabilities") or path.startswith("/api/auth/")
            if cloud_enabled() and path.startswith("/api/") and not public_api:
                session = auth_manager().resolve(self._auth_cookie())
                if session is None:
                    raise CloudError("Sign in to access your cloud workspace.", 401)
                CURRENT_CLOUD.set(session)
                CURRENT_OWNER.set(session.user()["id"])
            return handler()
        except CloudError as exc:
            return self._send(exc.status, {"error": str(exc)})
        finally:
            CURRENT_CLOUD.reset(cloud_token)
            CURRENT_OWNER.reset(owner_token)

    def do_GET(self):
        return self._dispatch(self._get)

    def do_POST(self):
        return self._dispatch(self._post)

    def do_PATCH(self):
        return self._dispatch(self._patch)

    def _session_id(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
            token = cookie["homely_session"].value if "homely_session" in cookie else ""
        except Exception:
            token = ""
        if not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
            token = secrets.token_urlsafe(32)
            self._new_cookie = token
        return token

    def _request_origin_allowed(self):
        port = self.server.server_port
        allowed_hosts = {"localhost:%s" % port, "127.0.0.1:%s" % port}
        if self.headers.get("Host", "") not in allowed_hosts:
            self._send(403, {"error": "Unrecognized local host."})
            return False
        origin = self.headers.get("Origin")
        if origin and origin not in {"http://" + h for h in allowed_hosts}:
            self._send(403, {"error": "Cross-origin requests are not allowed."})
            return False
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            self._send(403, {"error": "Cross-site requests are not allowed."})
            return False
        return True

    def _send(self, status, obj, *, attachment=False):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        if attachment:
            self.send_header("Content-Disposition", 'attachment; filename="homely-project-export.json"')
        if getattr(self, "_auth_set_cookie", None):
            self.send_header("Set-Cookie", self._auth_set_cookie)
        if getattr(self, "_new_cookie", None):
            self.send_header("Set-Cookie", "homely_session=" + self._new_cookie + "; HttpOnly; SameSite=Strict; Path=/")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValueError("Invalid request length.")
        if size <= 0 or size > MAX_JSON:
            raise ValueError("Request is empty or too large.")
        try:
            body = json.loads(self.rfile.read(size))
        except Exception:
            raise ValueError("Invalid JSON request.")
        if not isinstance(body, dict):
            raise ValueError("Expected a JSON object.")
        return body

    def _project_or_404(self, project_id):
        project = get_project(project_id)
        if project is None:
            self._send(404, {"error": "Project not found."})
        return project

    def _static(self, path):
        if path == "/":
            path = "/index.html"
        if path in ("/progress", "/progress/"):
            path = "/progress/index.html"
        file_path = (WEB / path.lstrip("/")).resolve()
        if not file_path.is_relative_to(WEB.resolve()) or not file_path.is_file():
            self._send(404, {"error": "Not found."})
            return
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(str(file_path))[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _get(self):
        if not self._request_origin_allowed():
            return
        path = urlparse(self.path).path
        parts = path.strip("/").split("/")
        if path == "/api/capabilities":
            try:
                watching = price_watch_store().running
            except ValueError:
                watching = False
            return self._send(200, {"passwordRecovery": cloud_enabled(), "confirmationResend": cloud_enabled(),
                "priceWatch": watching, "priceWatchReason": "Checks run only while this local server is running. Notifications appear in the app when you return; no email or push delivery." if watching else "Monitoring is paused; no checks or notifications can be promised."})
        if path == "/api/health":
            return self._send(200, {"ok": True, "openaiConfigured": bool(api_key()), "storageMode": "cloud" if cloud_enabled() else "local"})
        if path == "/api/auth/session":
            if not cloud_enabled():
                return self._send(200, {"mode": "local", "authenticated": False, "user": None})
            user = auth_manager().public_user(self._auth_cookie())
            return self._send(200, {"mode": "cloud", "authenticated": user is not None, "user": user})
        if path == "/api/progress":
            from backend.progress import build_progress
            return self._send(200, build_progress())
        if path == "/api/privacy/export":
            from backend.privacy import build_project_export, PrivacyExportError
            try:
                # _dispatch established the authenticated owner context first.
                # Do not use request selectors or fall back to local on failure.
                projects = cloud_store().list_for_export() if cloud_enabled() else list_projects()
                export = build_project_export(projects)
            except PrivacyExportError:
                return self._send(422, {"error": "Project data could not be exported safely."})
            except CloudError as exc:
                if exc.status == 413:
                    return self._send(413, {"error": "Project export exceeded its project or page limit; no partial export was returned."})
                status = exc.status if exc.status in (401, 403, 429, 502, 503, 504) else 503
                return self._send(status, {"error": "Project export could not complete. Try again later."})
            except Exception:
                return self._send(500, {"error": "Project export could not complete. Try again later."})
            return self._send(200, export, attachment=True)
        if path == "/api/watches":
            store = price_watch_store()
            owner = watch_owner()
            return self._send(200, {"watches": store.list(owner), "notifications": store.notifications(owner),
                "delivery": "in_app", "schedulerRunning": store.running,
                "deliveryNote": "Checks run only while this local server runs. Read notifications here when you return; no email or push delivery."})
        if path == "/api/projects":
            return self._send(200, {"projects": list_projects()})
        if len(parts) == 3 and parts[:2] == ["api", "projects"]:
            project = self._project_or_404(parts[2])
            return self._send(200, {"project": project}) if project else None
        if len(parts) == 4 and parts[:2] == ["api", "projects"] and parts[3] == "fit":
            project = self._project_or_404(parts[2])
            if project is None:
                return
            from backend.fit import gate_requirements, assess_candidate
            return self._send(200, {"gate": gate_requirements(project["brief"]),
                "candidates": [{"candidateId": candidate["id"], **assess_candidate(project["brief"], candidate)} for candidate in project["candidates"]]})
        if len(parts) == 4 and parts[:2] == ["api", "projects"] and parts[3] == "visualizations":
            project = self._project_or_404(parts[2])
            return self._send(200, {"jobs": visualization_history(project)}) if project else None
        if len(parts) == 3 and parts[:2] == ["api", "jobs"]:
            job = served_job(get_job(parts[2]))
            return self._send(200 if job else 404, {"job": job} if job else {"error": "Job not found."})
        if len(parts) == 3 and parts[:2] == ["api", "cloud-assets"]:
            if not cloud_enabled():
                raise CloudError("Cloud storage is not enabled.", 404)
            raw, mime = cloud_store().read(parts[2])
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Cache-Control", "private, no-store")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            return self.wfile.write(raw)
        if len(parts) == 3 and parts[:2] == ["api", "assets"]:
            if cloud_enabled():
                raise CloudError("Local assets are not exposed in cloud mode.", 404)
            filename = parts[2]
            if not re.fullmatch(r"[a-f0-9-]{36}\.(png|jpg|webp)", filename):
                return self._send(404, {"error": "Asset not found."})
            asset = ASSETS / filename
            if not asset.is_file():
                return self._send(404, {"error": "Asset not found."})
            raw = asset.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(filename)[0] or "application/octet-stream")
            self.send_header("Cache-Control", "private, no-store")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            return self.wfile.write(raw)
        if path.startswith("/api/"):
            return self._send(404, {"error": "API route not found."})
        return self._static(path)

    def _post(self):
        if not self._request_origin_allowed():
            return
        path = urlparse(self.path).path
        parts = path.strip("/").split("/")
        try:
            body = self._body()
            if path in ("/api/auth/sign-in", "/api/auth/sign-up", "/api/auth/sign-out", "/api/auth/recover", "/api/auth/resend", "/api/auth/reset"):
                if not cloud_enabled():
                    raise CloudError("Cloud sign-in is not enabled.", 503)
                manager = auth_manager()
                if path.endswith("recover"):
                    return self._send(200, manager.recover(body.get("email")))
                if path.endswith("resend"):
                    return self._send(200, manager.resend(body.get("email")))
                if path.endswith("reset"):
                    result = manager.reset_password(body.get("tokenHash"), body.get("newPassword"))
                    self._auth_set_cookie = "homely_auth=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"
                    return self._send(200, result)
                if path.endswith("sign-up"):
                    return self._send(200, manager.sign_up(body.get("email"), body.get("password")))
                if path.endswith("sign-out"):
                    result = manager.sign_out(self._auth_cookie())
                    self._auth_set_cookie = "homely_auth=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"
                    return self._send(200, result)
                result = manager.sign_in(body.get("email"), body.get("password"))
                self._auth_set_cookie = "homely_auth=" + result["session_id"] + "; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800"
                return self._send(200, {"user": result["user"]})
            if len(parts) == 4 and parts[:2] == ["api", "notifications"] and parts[3] == "read":
                return self._send(200, {"notification": price_watch_store().mark_read(watch_owner(), parts[2])})
            if len(parts) == 4 and parts[:2] == ["api", "watches"] and parts[3] == "cancel":
                return self._send(200, {"watch": price_watch_store().cancel(watch_owner(), parts[2])})
            if path == "/api/transcriptions":
                from backend.assistant import transcribe_audio
                return self._send(200, {"text": transcribe_audio(body.get("dataUrl"), body.get("consent"), api_key())})
            if len(parts) == 4 and parts[:2] == ["api", "jobs"] and parts[3] == "cancel":
                with LOCK:
                    job = get_job(parts[2])
                    if job is None:
                        return self._send(404, {"error": "Job not found."})
                    if job["status"] in ("queued", "running"):
                        update_job(job["id"], status="cancelled", progress="Cancelled; no late results will replace your project")
                    return self._send(200, {"job": get_job(job["id"])})
            if path == "/api/projects":
                name = str(body.get("name", "")).strip()[:100]
                mode = body.get("mode", "pro")
                if not name or mode not in ("pro", "diy"):
                    raise ValueError("Name and valid mode are required.")
                project = {
                    "id": str(uuid.uuid4()), "name": name, "mode": mode,
                    "version": 1, "createdAt": now_iso(), "updatedAt": now_iso(),
                    "brief": {"itemType": "furniture", "quantity": 1, "style": "", "location": "",
                              "flexibleTarget": None, "hardCap": None, "notes": "",
                              "measurements": {"tableUndersideIn": None, "chairArmIn": None,
                                               "roomWidthIn": None, "roomDepthIn": None}},
                    "room": None, "candidates": [], "decisions": [],
                }
                save_project(project)
                return self._send(201, {"project": project})
            if len(parts) == 4 and parts[:2] == ["api", "projects"]:
                project = self._project_or_404(parts[2])
                if project is None:
                    return
                action = parts[3]
                if action == "watches":
                    owner = watch_owner()
                    with LOCK:
                        project = current_version(project["id"], body.get("expectedVersion"))
                        if body.get("enabled") is False:
                            return self._send(200, {"watch": price_watch_store().cancel(owner, body.get("watchId"))})
                        if body.get("enabled") is not True:
                            raise ValueError("Explicit product-specific opt-in is required.")
                        candidate = next((c for c in project["candidates"] if c["id"] == body.get("candidateId")), None)
                        if candidate is None:
                            raise ValueError("Select a current product from this project.")
                        product = copy.deepcopy(candidate)
                    return self._send(201, {"watch": price_watch_store().subscribe(owner, product, consent=True),
                        "deliveryNote": "Checks run only while this local server runs. Notifications are in-app only; no email or push delivery."})
                if action == "fit-evidence":
                    from backend.fit import validate_candidate_evidence
                    with LOCK:
                        project = current_version(project["id"], body.get("expectedVersion"))
                        candidate = next((c for c in project["candidates"] if c["id"] == body.get("candidateId")), None)
                        if candidate is None:
                            raise ValueError("Select a product from this project.")
                        candidate["fitEvidence"] = validate_candidate_evidence(body.get("fitEvidence"), candidate)
                        project["version"] += 1
                        project["updatedAt"] = now_iso()
                        save_project(project)
                    return self._send(200, {"project": project})
                if action == "retained-product":
                    from backend.sourcing import SourcingError, enrich_product_url
                    with LOCK:
                        current_version(project["id"], body.get("expectedVersion"))
                    url = body.get("url")
                    if not isinstance(url, str) or len(url) > 2048:
                        raise ValueError("Enter one public product URL.")
                    try:
                        product = enrich_product_url(url, {**project["brief"], "itemType": "retained furniture"})
                    except SourcingError as exc:
                        return self._send(422, {"error": str(exc)})
                    with LOCK:
                        current_version(project["id"], body.get("expectedVersion"))
                    return self._send(200, {"product": {k: product.get(k) for k in ("title", "url", "exactSku", "variant", "dimensions", "fieldEvidence")}, "requiresConfirmation": True})
                if action == "review-preview":
                    from backend.review_snapshot import build_review_snapshot, ReviewSnapshotError
                    if set(body) - {"expectedVersion", "scope"}:
                        raise ValueError("Unsupported review-preview request fields.")
                    expected = body.get("expectedVersion")
                    if type(expected) is not int or expected < 1:
                        raise ValueError("A positive expected project version is required.")
                    scope = body.get("scope", {})
                    if not isinstance(scope, dict):
                        raise ValueError("Disclosure scope must be an object.")
                    with LOCK:
                        authorized = current_version(project["id"], expected)
                        # Browser asset IDs/URLs cannot establish image ownership.
                        if scope.get("imageIds", []) != []:
                            raise ValueError("Image selection is not available in review preview yet.")
                        try:
                            preview = build_review_snapshot(copy.deepcopy(authorized), scope, assets=[])
                        except ReviewSnapshotError:
                            raise ValueError("Review selection is invalid or unavailable in this project.") from None
                    return self._send(200, {"preview": preview, "canCreateReview": False})
                if action == "assistant":
                    return self._send(200, assistant_request(project["id"], body, self._session_id()))
                if action == "room":
                    if body.get("uploadConsent") is not True and body.get("consent") is not True:
                        raise ValueError("Room-photo upload consent is required.")
                    expected = body.get("expectedVersion", project["version"])
                    with LOCK:
                        current_version(project["id"], expected)
                    _, url = save_asset(body.get("dataUrl"), project["id"], "room_original", True)
                    with LOCK:
                        project = current_version(project["id"], expected)
                        project["room"] = {"imageUrl": url, "uploadedAt": now_iso(), "uploadConsent": True, "consent": body.get("consent") is True}
                        for retained in project["brief"].get("journey", {}).get("retainedObjects", []):
                            retained.pop("anchor", None)
                        project["version"] += 1
                        project["updatedAt"] = now_iso()
                        save_project(project)
                    return self._send(200, {"project": project})
                if action == "research":
                    return self._send(202, {"job": start_research(project["id"], body.get("expectedVersion", project["version"]), body.get("mode", "fit"))})
                if action == "product-urls":
                    from backend.sourcing import SourcingError, enrich_product_url, verify_candidate
                    url = body.get("url")
                    if not isinstance(url, str) or len(url) > 2048:
                        raise ValueError("Enter one public product URL.")
                    try:
                        candidate = verify_candidate(enrich_product_url(url, project["brief"]), project["brief"])
                    except SourcingError as exc:
                        return self._send(422, {"error": str(exc)})
                    with LOCK:
                        current = get_project(project["id"])
                        if current["version"] != project["version"]:
                            return self._send(409, {"error": "Project changed during import. Retry on the current brief."})
                        if any(c.get("url") == candidate.get("url") for c in current["candidates"]):
                            return self._send(409, {"error": "This product URL is already in your research."})
                        current["candidates"].append(candidate)
                        current["version"] += 1
                        current["updatedAt"] = now_iso()
                        save_project(current)
                    return self._send(201, {"candidate": candidate, "project": current})
                if action == "visualizations":
                    expected = body.get("expectedVersion", project["version"])
                    with LOCK:
                        project = current_version(project["id"], expected)
                    candidate_id = body.get("candidateId")
                    if not any(c["id"] == candidate_id for c in project["candidates"]):
                        raise ValueError("Select a saved candidate.")
                    if project.get("room") is None:
                        raise ValueError("Upload a room photo first.")
                    if body.get("productImageRightsConfirmed") is not True:
                        raise ValueError("Confirm rights to use the product reference image.")
                    product_path, product_url = save_asset(body.get("productImageDataUrl"), project["id"], "product_source", True)
                    output_path = asset_directory() / (str(uuid.uuid4()) + ".png")
                    with LOCK:
                        current_version(project["id"], expected)
                        job = new_job(project["id"], "visualization")
                        job["candidateId"] = candidate_id
                        job["projectVersion"] = project["version"]
                        save_job(job)
                        snapshot = copy.deepcopy(project)
                    background(visualization_worker, job["id"], project["id"], candidate_id, product_path, output_path, True, product_url, snapshot)
                    return self._send(202, {"job": job})
                if action == "decisions":
                    decision, changed = record_decision(project["id"], body.get("expectedVersion", project["version"]), body.get("candidateId"))
                    return self._send(201, {"decision": decision, "project": changed})
                if action == "handoff":
                    candidate = next((c for c in project["candidates"] if c["id"] == body.get("candidateId")), None)
                    if candidate is None:
                        raise ValueError("Candidate not found.")
                    total = delivered_total(candidate, project["brief"]["quantity"])
                    cap = project["brief"].get("hardCap")
                    if candidate.get("status") != "ready":
                        return self._send(200, {"status": "blocked", "url": None, "reason": "Exact variant and quantity are not verified."})
                    if total is None or cap is None or total > float(cap):
                        return self._send(200, {"status": "blocked", "url": None, "reason": "Delivered total is unknown or exceeds the hard cap."})
                    return self._send(200, {"status": "blocked", "url": None, "reason": "Fresh source-specific stock and price recheck is not yet connected."})
            return self._send(404, {"error": "API route not found."})
        except CloudError as exc:
            return self._send(exc.status, {"error": str(exc)})
        except AssistantError as exc:
            return self._send(exc.status, {"error": str(exc), "code": exc.code})
        except ConflictError as exc:
            return self._send(409, {"error": str(exc)})
        except ValueError as exc:
            return self._send(400, {"error": str(exc)})
        except Exception:
            return self._send(500, {"error": "Internal server error."})

    def _patch(self):
        if not self._request_origin_allowed():
            return
        path = urlparse(self.path).path
        parts = path.strip("/").split("/")
        if len(parts) != 4 or parts[:2] != ["api", "projects"] or parts[3] != "brief":
            return self._send(404, {"error": "API route not found."})
        try:
            body = self._body()
            project = patch_brief(parts[2], body.get("expectedVersion"), body.get("brief"))
            return self._send(200, {"project": project})
        except CloudError as exc:
            return self._send(exc.status, {"error": str(exc)})
        except AssistantError as exc:
            return self._send(exc.status, {"error": str(exc), "code": exc.code})
        except ConflictError as exc:
            return self._send(409, {"error": str(exc)})
        except (TypeError, ValueError) as exc:
            return self._send(400, {"error": str(exc)})
        except Exception:
            return self._send(500, {"error": "Internal server error."})


def main():
    ensure_dirs()
    port = int(os.environ.get("HOMELY_PORT", "8765"))
    price_watch_store()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("Homely local preview: http://127.0.0.1:%d" % port, flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
