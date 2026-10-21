"""Ten real website chat calls; prints counts and timing, never the API key or replies."""
import concurrent.futures
import http.cookiejar
import json
import time
import urllib.error
import urllib.request
import uuid

BASE = 'http://127.0.0.1:8002'


class Client:
    def __init__(self):
        self.csrf = ''
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def call(self, path, payload):
        request = urllib.request.Request(
            BASE + path,
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json', 'X-CSRF-Token': self.csrf},
        )
        try:
            response = self.opener.open(request, timeout=220)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            value = json.load(response)
            if 'csrf' in value:
                self.csrf = value['csrf']
            return response.status, value


admin = Client()
assert admin.call('/api/login', {'kind': 'admin', 'id': 'admin', 'password': 'test-admin-123'})[0] == 200
for i in range(10):
    code, result = admin.call('/api/admin/create', {'id': f'REAL{i:02d}', 'password': 'test-student-123', 'group_code': 'experimental'})
    assert code == 200, result


def run(i):
    client = Client()
    participant = f'REAL{i:02d}'
    assert client.call('/api/login', {'id': participant, 'password': 'test-student-123'})[0] == 200
    assert client.call('/api/consent', {'agree': True})[0] == 200
    start = time.monotonic()
    code, reply = client.call('/api/chat', {
        'text': '食堂高峰排队较长，我该先记录哪些观察信息？',
        'request_id': str(uuid.uuid4()),
    })
    return {'participant': participant, 'http_status': code, 'reply_present': bool(reply.get('reply')),
            'seconds': round(time.monotonic() - start, 2)}


with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    results = list(pool.map(run, range(10)))
print('HTTP success:', sum(r['http_status'] == 200 for r in results), '/ 10')
print('Replies shown:', sum(r['reply_present'] for r in results), '/ 10')
print('Duration seconds:', min(r['seconds'] for r in results), '-', max(r['seconds'] for r in results))
print('HTTP status codes:', [r['http_status'] for r in results])
