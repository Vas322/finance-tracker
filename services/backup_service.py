import os
import zipfile
import json
import logging
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError
from config import Config
from database import backup_db

logger = logging.getLogger(__name__)

YANDEX_API = 'https://cloud-api.yandex.net/v1/disk'
YANDEX_FOLDER = '/finance-tracker-backups'
MAX_REMOTE_BACKUPS = 30


def get_headers():
    token = Config.YANDEX_DISK_TOKEN
    if not token:
        return None
    return {'Authorization': f'OAuth {token}', 'Content-Type': 'application/json'}


def _api_request(method, url, data=None, quiet=False):
    headers = get_headers()
    if not headers:
        return None
    req = Request(url, method=method, headers=headers)
    if data is not None:
        req.data = json.dumps(data).encode()
    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {}
    except URLError as e:
        if not quiet:
            logger.error('Yandex API error %s %s: %s', method, url, e)
        return None


def ensure_folder():
    _api_request('PUT', f'{YANDEX_API}/resources?path={YANDEX_FOLDER}', quiet=True)


def get_upload_url(filename):
    path = f'{YANDEX_FOLDER}/{filename}'
    url = f'{YANDEX_API}/resources/upload?path={path}&overwrite=true'
    result = _api_request('GET', url)
    if result and 'href' in result:
        return result['href']
    return None


def upload_file(local_path, remote_filename):
    upload_url = get_upload_url(remote_filename)
    if not upload_url:
        logger.error('Failed to get upload URL from Yandex Disk')
        return False
    try:
        with open(local_path, 'rb') as f:
            data = f.read()
        req = Request(upload_url, method='PUT', data=data)
        with urlopen(req, timeout=120) as resp:
            if resp.status in (200, 201, 202):
                logger.info('Uploaded %s to Yandex Disk', remote_filename)
                return True
            logger.error('Upload failed with status %s', resp.status)
            return False
    except URLError as e:
        logger.error('Upload error: %s', e)
        return False


def list_remote_backups():
    url = f'{YANDEX_API}/resources?path={YANDEX_FOLDER}&sort=-created&limit=100'
    result = _api_request('GET', url, quiet=True)
    if result is None or 'error' in result:
        return None
    if '_embedded' in result and 'items' in result['_embedded']:
        return [item for item in result['_embedded']['items'] if not item.get('type') == 'dir']
    return None


def delete_remote(path):
    url = f'{YANDEX_API}/resources?path={path}&permanently=true'
    _api_request('DELETE', url)


def cleanup_old_backups():
    files = list_remote_backups()
    if files is None:
        return
    if len(files) > MAX_REMOTE_BACKUPS:
        to_delete = files[MAX_REMOTE_BACKUPS:]
        for item in to_delete:
            delete_remote(item['path'])
            logger.info('Deleted old remote backup: %s', item['name'])


def create_app_archive():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backup_dir = os.path.join(base_dir, 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    archive_name = f'finance-tracker-{timestamp}.zip'
    archive_path = os.path.join(backup_dir, archive_name)

    exclude_dirs = {'venv', '.git', '__pycache__', 'backups', '.idea', '.vscode'}
    exclude_ext = {'.pyc', '.pyo'}

    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            rel_root = os.path.relpath(root, base_dir)
            if rel_root == '.':
                rel_root = ''
            for file in files:
                if os.path.splitext(file)[1] in exclude_ext:
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.join(rel_root, file) if rel_root else file
                zf.write(file_path, arcname)

    logger.info('Created archive: %s', archive_path)
    return archive_path


def run_backup():
    backup_db()
    if not Config.YANDEX_DISK_TOKEN:
        logger.info('YANDEX_DISK_TOKEN not set, skipping Yandex Disk backup')
        return

    ensure_folder()
    archive_path = create_app_archive()
    if not archive_path:
        logger.error('Failed to create archive')
        return

    try:
        filename = os.path.basename(archive_path)
        upload_file(archive_path, filename)
        cleanup_old_backups()
    finally:
        os.remove(archive_path)




