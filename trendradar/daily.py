"""Local daily delivery, separate from the legacy notification scheduler."""
import io
import json
import os
import sys
import time
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path

from trendradar.utils.time import get_configured_time


class RedactedLog(io.TextIOBase):
    """Redact complete lines, including credentials split across write calls."""
    def __init__(self, stream):
        self.stream = stream
        self.pending = ''

    def write(self, text):
        self.pending += text
        while '\n' in self.pending:
            line, self.pending = self.pending.split('\n', 1)
            self.stream.write(self.redact(line) + '\n')
            self.stream.flush()
        return len(text)

    @staticmethod
    def redact(text):
        values = {os.environ.get(name, '') for name in ('AI_API_KEY','AI_API_BASE')}
        for value in sorted(values - {''}, key=len, reverse=True):
            text = text.replace(value, '<REDACTED>')
        return text

    def flush(self):
        if not self.stream.closed:
            self.stream.flush()

    def finish(self):
        if self.pending:
            self.stream.write(self.redact(self.pending))
            self.pending = ''
        self.stream.flush()


@contextmanager
def daily_lock(path):
    """OS releases the lock after crashes; a stale filename never blocks retries."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        if path.stat().st_size == 0:
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            acquired = False
        else:
            acquired = True
        try:
            yield acquired
        finally:
            if acquired:
                stream.seek(0)
                if os.name == 'nt':
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(stream, fcntl.LOCK_UN)


def save_json(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temporary, path)


def cleanup(root, now=None, days=30):
    """Only direct files in two owned cache/log folders; retain all reports."""
    cutoff = (time.time() if now is None else now) - days * 86400
    removed = 0
    for relative, pattern in [('output/daily/logs', '*.log'), ('output/evidence', '*.json')]:
        folder = (root/relative).resolve()
        # Do not follow a folder junction/symlink outside this workspace.
        if not folder.is_relative_to(root.resolve()):
            continue
        for path in folder.glob(pattern):
            if path.is_symlink() or path.resolve().parent != folder:
                continue
            try:
                if path.is_file() and path.stat().st_mtime < cutoff:
                    path.unlink()
                    removed += 1
            except OSError:
                pass  # Cleanup cannot invalidate a successfully delivered report.
    return removed


def run_daily(root=None, now=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    root = root.resolve()
    current = now or get_configured_time('Asia/Shanghai')
    date = current.strftime('%Y-%m-%d')
    daily = root/'output'/'daily'
    with daily_lock(daily/'run.lock') as acquired:
        if not acquired:
            return 0
        record_path = daily/'runs'/f'{date}.json'
        if record_path.exists():
            previous = json.loads(record_path.read_text(encoding='utf-8'))
            if previous.get('completed'):
                return 0
        stamp = current.strftime('%Y%m%d-%H%M%S-%f')
        log_path = daily/'logs'/f'{stamp}.log'
        log_path.parent.mkdir(parents=True, exist_ok=True)
        record = dict(date=date, timezone='Asia/Shanghai', status='running', completed=False,
                      started_at=current.isoformat(), log=str(log_path))
        save_json(record_path, record)
        save_json(daily/'latest.json', record)
        os.environ.setdefault('LITELLM_LOCAL_MODEL_COST_MAP', 'True')
        os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
        with log_path.open('w', encoding='utf-8') as stream:
            log = RedactedLog(stream)
            with redirect_stdout(log), redirect_stderr(log):
                try:
                    from trendradar.preview import run_preview
                    code = run_preview(no_open=True, days=7)
                except Exception as exc:
                    print(f'Daily run failed: {type(exc).__name__}: {exc}')
                    code = 1
                finally:
                    log.finish()
            record.update(status='completed' if code == 0 else 'failed', completed=code == 0,
                          exit_code=code, finished_at=get_configured_time('Asia/Shanghai').isoformat())
            save_json(record_path, record)
            save_json(daily/'latest.json', record)
        cleanup(root)
        return code


if __name__ == '__main__':
    sys.exit(run_daily())
