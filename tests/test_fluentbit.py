"""Opt-in replay against the pinned binary; no AWS/Kubernetes calls are made.

PANORAMA_TEST_FLUENTBIT_IMAGE=<locally pulled image> python -m pytest tests/test_fluentbit.py
"""
import json
import os
import subprocess
import uuid
import gzip
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from test_verawood import render

IMAGE = os.environ.get("PANORAMA_TEST_FLUENTBIT_IMAGE")
pytestmark = pytest.mark.skipif(not IMAGE, reason="Set PANORAMA_TEST_FLUENTBIT_IMAGE for local Docker replay")


@pytest.mark.parametrize("runtime", ["local", "docker", "cri"])
def test_replay_tracking_records(tmp_path, runtime):
    event = '{"event_type":"test","value":"Unicode ñ and {braces}"}'
    message = f'2026-09-08 10:00:00,000 INFO 1 [tracking] [user 3] [ip 192.0.2.1] logger.py:12 - {event}'
    ordinary = '2026-09-08 10:00:00,000 INFO 1 [app] ordinary application log'
    lines = []
    if runtime == "local":
        lines = [event, ordinary, 'x' * (1024 * 1024 + 1), event + '\r', 'broken JSON without braces']
        config = render("templates/panorama/apps/panorama-elt/fluent-bit-local.conf")
        config = config.replace('/openedx/data/logs/tracking.log', '/fixtures/input.log')
    else:
        if runtime == "docker":
            midpoint = len(message) // 2
            lines = [json.dumps({"log": line, "stream": "stdout", "time": "2026-09-08T10:00:00.000000000Z"}) for line in [message + '\n', ordinary + '\n', message[:midpoint], message[midpoint:] + '\n']]
        else:
            midpoint = len(message) // 2
            lines = [f'2026-09-08T10:00:00.000000000Z stdout F {message}',
                     f'2026-09-08T10:00:01.000000000Z stdout F {ordinary}',
                     f'2026-09-08T10:00:02.000000000Z stdout P {message[:midpoint]}',
                     f'2026-09-08T10:00:02.000000000Z stdout F {message[midpoint:]}']
        config = render("templates/panorama/apps/panorama-elt/fluent-bit.conf")
        source_path = '/var/log/containers/lms*.log'
        assert source_path in config, "Replay must redirect the configured tail input"
        config = config.replace(source_path, '/fixtures/input.log')
        # Kubernetes metadata needs a real API; this replay tests transport and event parsing.
        start = config.index('[FILTER]')
        end = config.index('[FILTER]', start + 1)
        config = config[:start] + config[end:]
    config = config[:config.index('[OUTPUT]')] + '[OUTPUT]\n    Name stdout\n    Match *\n    Format json_lines\n'
    config = config.replace('parsers.conf', '/fixtures/parsers.conf')
    config = config.replace('/var/lib/panorama-fluentbit/tail.db', '/tmp/tail.db')
    config = config.replace('Name tail', 'Name tail\n    Read_from_Head On').replace('Name              tail', 'Name              tail\n    Read_from_Head On')
    (tmp_path / 'input.log').write_text('\n'.join(lines) + '\n')
    (tmp_path / 'flb.conf').write_text(config)
    (tmp_path / 'parsers.conf').write_text(render('templates/panorama/apps/panorama-elt/parsers.conf'))
    name = f'panorama-replay-{uuid.uuid4().hex}'
    try:
        result = subprocess.run([
            'docker', 'run', '--rm', '--name', name, '--network', 'none', '-v', f'{tmp_path}:/fixtures:ro',
            '--entrypoint', '/bin/sh', IMAGE, '-c',
            '/fluent-bit/bin/fluent-bit -c /fixtures/flb.conf > /tmp/replay.log 2>&1 & collector_pid=$!; '
            'for attempt in $(seq 1 45); do grep -q "inotify_fs_add" /tmp/replay.log && break; sleep 1; done; '
            'sleep 8; kill -TERM "$collector_pid"; wait "$collector_pid"; result=$?; cat /tmp/replay.log; exit "$result"',
        ], capture_output=True, text=True, timeout=90)
    finally:
        subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr
    records = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
    assert len(records) == 2, (result.stdout, result.stderr)
    assert all(record['event'] == event for record in records), records


def test_gzip_ndjson_and_consumer_key_in_local_sink(tmp_path):
    """Use only a disposable HTTP sink with fake credentials, never an AWS endpoint."""
    objects = []

    class Sink(BaseHTTPRequestHandler):
        def do_PUT(self):  # pylint: disable=invalid-name
            objects.append((self.path, self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(200)
            self.send_header('ETag', '"panorama-test"')
            self.send_header('Content-Length', '0')
            self.end_headers()

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(('0.0.0.0', 0), Sink)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    event = '{"event_type":"sink-test","value":"ñ"}'
    config = render('templates/panorama/apps/panorama-elt/fluent-bit-local.conf',
                    PANORAMA_BUCKET='panorama-test', PANORAMA_RAW_LOGS_BUCKET='panorama-test',
                    PANORAMA_LOGS_TOTAL_FILE_SIZE='1M', PANORAMA_LOGS_UPLOAD_TIMEOUT='1s')
    config = config.replace('/openedx/data/logs/tracking.log', '/fixtures/input.log')
    config = config.replace('Name tail', 'Name tail\n    Read_from_Head On')
    config = config.replace('parsers.conf', '/fixtures/parsers.conf').replace('/var/lib/panorama-fluentbit', '/tmp/panorama')
    config = config.replace('Name             s3', f'Name             s3\n    endpoint http://host.docker.internal:{server.server_port}\n    tls Off')
    (tmp_path / 'flb.conf').write_text(config)
    (tmp_path / 'parsers.conf').write_text(render('templates/panorama/apps/panorama-elt/parsers.conf'))
    (tmp_path / 'input.log').write_text(event + '\n')
    name = f'panorama-sink-{uuid.uuid4().hex}'
    try:
        result = subprocess.run([
            'docker', 'run', '--rm', '--name', name,
            '--add-host', 'host.docker.internal:host-gateway', '-v', f'{tmp_path}:/fixtures:ro',
            '-e', 'AWS_ACCESS_KEY_ID=test', '-e', 'AWS_SECRET_ACCESS_KEY=test', '-e', 'AWS_EC2_METADATA_DISABLED=true',
            '--entrypoint', '/bin/sh', IMAGE, '-c',
            'mkdir -p /tmp/panorama; /fluent-bit/bin/fluent-bit -c /fixtures/flb.conf > /tmp/replay.log 2>&1 & collector_pid=$!; '
            'for attempt in $(seq 1 45); do grep -q "inotify_fs_add" /tmp/replay.log && break; sleep 1; done; '
            'sleep 8; kill -TERM "$collector_pid"; wait "$collector_pid"; result=$?; cat /tmp/replay.log; exit "$result"',
        ], capture_output=True, text=True, timeout=90)
    finally:
        subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=20)
        server.shutdown()
        server.server_close()
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert objects, (result.stdout, result.stderr)
    assert all(key.startswith('/panorama-test/openedx/tracking_logs/lms=courses.example.org/year=') for key, _ in objects)
    assert all(key.endswith('.gz') for key, _ in objects)
    assert b''.join(gzip.decompress(body) for _, body in objects).decode().splitlines() == [event]
