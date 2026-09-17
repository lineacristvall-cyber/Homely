"""Isolated, non-destructive stock-photo UI fixture. Product URL import enabled; paid API key disabled."""
from pathlib import Path
import argparse, base64, copy, hashlib, json, os, sys
ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ['HOMELY_STORAGE'] = 'local'
os.environ['OPENAI_API_KEY'] = ''
from backend import server as app
from backend.cloud.project_store import _document, _validated_image


def validate():
    manifest = json.loads((FIXTURE / 'manifest.json').read_text())
    project = json.loads((FIXTURE / 'project.json').read_text())
    raw = (FIXTURE / manifest['asset']['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == manifest['asset']['sha256'], 'Asset checksum mismatch'
    _validated_image(raw, 'image/jpeg')
    app.validate_brief({}, project['brief'])
    _document(project)
    assert project['room']['consent'] is False
    assert all(v is None for v in project['brief']['measurements'].values())
    assert all(c['status'] == 'lead' and c['availableQuantity'] is None and c['imageUrl'] is None for c in project['candidates'])
    return manifest, project, raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path('/private/tmp/homely-stock-fixture-v1'))
    parser.add_argument('--port', type=int, default=8768)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--seed-only', action='store_true')
    args = parser.parse_args()
    manifest, project, raw = validate()
    if args.check:
        print('PASS: image checksum/decode, app brief and cloud document shape, unknown measurements, image consent and lead-only candidates.')
        return
    target = args.data_dir.expanduser().resolve()
    if target == (ROOT/'data').resolve() or target == ROOT or ROOT in target.parents:
        raise SystemExit('Use a separate data directory outside the repository.')
    marker = target/'.homely-stock-fixture-v1'
    if target.exists() and any(target.iterdir()) and (not marker.is_file() or marker.read_text() != manifest['schemaVersion']):
        raise SystemExit('Refusing a nonempty directory not owned by this fixture.')
    target.mkdir(parents=True, exist_ok=True)
    marker.write_text(manifest['schemaVersion'])
    app.DATA = target
    app.PROJECTS, app.ASSETS, app.JOBS = target/'projects', target/'assets', target/'jobs'
    app.ensure_dirs()
    destination = app.PROJECTS/(project['id']+'.json')
    if destination.exists():
        print('Existing fixture project retained; no edits overwritten.')
    else:
        _, asset_url = app.save_asset('data:image/jpeg;base64,'+base64.b64encode(raw).decode(), consent=False)
        seeded = copy.deepcopy(project)
        seeded['room'].update(imageUrl=asset_url, uploadedAt=app.now_iso())
        app.save_project(seeded)
        print('Seeded: '+seeded['name'])
    if args.seed_only:
        return
    app.api_key = lambda: None
    server = app.ThreadingHTTPServer(('127.0.0.1', args.port), app.Handler)
    print(f'Stock-photo fixture: http://127.0.0.1:{args.port}/', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
