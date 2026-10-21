"""Run with a local mock server at :8001 and Chrome DevTools at :9222."""
import http.cookiejar
import json
import urllib.request
import browser_flow as browser


opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def call(path, data, csrf=''):
    request = urllib.request.Request(
        'http://127.0.0.1:8001' + path,
        data=json.dumps(data).encode(),
        headers={'Content-Type': 'application/json', 'X-CSRF-Token': csrf},
    )
    with opener.open(request) as response:
        return json.load(response)


admin = call('/api/login', {'kind': 'admin', 'id': 'admin', 'password': 'test-admin-123'})
invite = call('/api/admin/invitations', {'count': 1, 'group_code': 'experimental'}, admin['csrf'])['codes'][0]
browser.c = browser.CDP(browser.target()['webSocketDebuggerUrl'])
browser.wait("document.querySelector('#show-register') !== null")
assert browser.c.eval("document.querySelector('#register').classList.contains('hidden')")
browser.c.eval("document.querySelector('#show-register').click(); true")
assert not browser.c.eval("document.querySelector('#register').classList.contains('hidden')")
browser.c.eval(
    "document.querySelector('#register-form [name=invite_code]').value=" + json.dumps(invite['invite_code']) + ";"
    "document.querySelector('#register-form [name=password]').value='browser-password-123';"
    "document.querySelector('#register-form [name=confirm_password]').value='browser-password-123';"
    "document.querySelector('#register-form').requestSubmit(); true"
)
browser.wait("!document.querySelector('#registration-result').classList.contains('hidden')")
assert invite['participant_id'] in browser.c.eval("document.querySelector('#registration-result').textContent")
browser.c.eval("document.querySelector('#close-register').click(); true")
assert browser.c.eval("document.querySelector('#login-form [name=id]').value") == invite['participant_id']
browser.c.eval("document.querySelector('#login-form [name=password]').value='browser-password-123'; document.querySelector('#login-form').requestSubmit(); true")
browser.wait("!document.querySelector('#student').classList.contains('hidden')")
browser.wait("!document.querySelector('#consent').classList.contains('hidden')")
print('PASS: browser invitation registration, displayed ID, login and consent')
