"""Smoke test for public deployment additions against an isolated local server."""
import http.cookiejar
import json
import urllib.error
import urllib.request
import uuid

BASE = 'http://127.0.0.1:8001'


class Client:
    def __init__(self):
        self.csrf = ''
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def call(self, path, payload=None):
        request = urllib.request.Request(
            BASE + path,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={'Content-Type': 'application/json', 'X-CSRF-Token': self.csrf},
        )
        try:
            response = self.opener.open(request)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            result = json.load(response)
            if 'csrf' in result:
                self.csrf = result['csrf']
            return response.status, result, response.headers


admin = Client()
assert admin.call('/api/login', {'kind': 'admin', 'id': 'admin', 'password': 'test-admin-123'})[0] == 200
status, invite_result, headers = admin.call('/api/admin/invitations', {'count': 2, 'group_code': 'experimental'})
assert status == 200 and len(invite_result['codes']) == 2
assert headers['X-Frame-Options'] == 'DENY'
pid, code = invite_result['codes'][0]['participant_id'], invite_result['codes'][0]['invite_code']
student = Client()
assert student.call('/api/register', {'invite_code': code, 'password': 'study-password-123'})[0] == 200
assert student.call('/api/register', {'invite_code': code, 'password': 'study-password-123'})[0] == 400
assert student.call('/api/login', {'id': pid, 'password': 'study-password-123'})[0] == 200
assert student.call('/api/admin/invitations', {'count': 1})[0] == 403
assert student.call('/api/consent', {'agree': True})[0] == 200
for i in range(20):
    assert student.call('/api/chat', {'text': f'第 {i} 轮观察', 'request_id': str(uuid.uuid4())})[0] == 200
assert student.call('/api/chat', {'text': '超过限额', 'request_id': str(uuid.uuid4())})[0] == 429
relogin = Client()
assert relogin.call('/api/login', {'id': pid, 'password': 'study-password-123'})[0] == 200
status, messages, _ = relogin.call('/api/messages')
assert status == 200 and len(messages['messages']) == 40
for _ in range(8):
    assert Client().call('/api/login', {'id': 'NONEXISTENT-TEST', 'password': 'wrong-password'})[0] == 401
assert Client().call('/api/login', {'id': 'NONEXISTENT-TEST', 'password': 'wrong-password'})[0] == 429
print('PASS: one-time invite, registration, role isolation, chat rate, login throttle, relogin history, security header')
