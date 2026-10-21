"""Browser-level login, chat rendering, and reload using Chrome DevTools Protocol."""
import base64, json, os, socket, struct, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['DATA_DIR']=os.environ.get('BROWSER_DATA_DIR','/private/tmp/cps-full-flow')
import server

db=server.connect()
if not db.execute('SELECT 1 FROM participants WHERE id=?',('BROWSER01',)).fetchone():
    db.execute('INSERT INTO participants(id,group_code,password_hash,created_at) VALUES(?,?,?,?)',('BROWSER01','experimental',server.hash_pw('student-123'),server.now()))
db.close()

def target():
    with urllib.request.urlopen('http://127.0.0.1:9222/json/list') as r: pages=json.load(r)
    return next(x for x in pages if x.get('type')=='page' and x.get('url','').startswith('http://127.0.0.1:8001/'))

class CDP:
    def __init__(self,url):
        from urllib.parse import urlparse
        p=urlparse(url);self.sock=socket.create_connection((p.hostname,p.port));self.buf=b'';self.id=0
        key=base64.b64encode(os.urandom(16)).decode()
        request=f'GET {p.path} HTTP/1.1\r\nHost: {p.hostname}:{p.port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nOrigin: http://127.0.0.1:8001\r\n\r\n'
        self.sock.sendall(request.encode())
        data=b''
        while b'\r\n\r\n' not in data:data+=self.sock.recv(4096)
        head,self.buf=data.split(b'\r\n\r\n',1)
        assert b' 101 ' in head,head[:300]
    def exact(self,n):
        while len(self.buf)<n:self.buf+=self.sock.recv(4096)
        out,self.buf=self.buf[:n],self.buf[n:]
        return out
    def read(self):
        while True:
            h=self.exact(2);opcode=h[0]&15;length=h[1]&127
            if length==126:length=struct.unpack('!H',self.exact(2))[0]
            if length==127:length=struct.unpack('!Q',self.exact(8))[0]
            data=self.exact(length)
            if opcode==1:return json.loads(data)
            if opcode==8:raise RuntimeError('Chrome closed DevTools socket')
    def send(self,method,params=None):
        self.id+=1;body=json.dumps({'id':self.id,'method':method,'params':params or {}}).encode();mask=os.urandom(4)
        size=len(body);header=b'\x81'+(bytes([0x80|size]) if size<126 else b'\xfe'+struct.pack('!H',size) if size<65536 else b'\xff'+struct.pack('!Q',size))
        self.sock.sendall(header+mask+bytes(x^mask[i%4] for i,x in enumerate(body)))
        while True:
            result=self.read()
            if result.get('id')==self.id:
                if 'error' in result:raise RuntimeError(result['error'])
                return result.get('result',{})
    def eval(self,expression):
        r=self.send('Runtime.evaluate',{'expression':expression,'returnByValue':True,'awaitPromise':True})
        if 'exceptionDetails' in r:raise RuntimeError(r['exceptionDetails'])
        return r.get('result',{}).get('value')

def wait(expr,seconds=15):
    start=time.time()
    while time.time()-start<seconds:
        try:
            if c.eval(expr):return
        except Exception:pass
        time.sleep(.2)
    raise AssertionError('Browser condition timed out: '+expr)

if __name__=='__main__':
    c=CDP(target()['webSocketDebuggerUrl'])
    wait("document.querySelector('#login-form') !== null")
    c.eval("document.querySelector('#login-form [name=id]').value='BROWSER01'; document.querySelector('#login-form [name=password]').value='student-123'; document.querySelector('#login-form').requestSubmit(); true")
    wait("!document.querySelector('#student').classList.contains('hidden')")
    wait("!document.querySelector('#consent').classList.contains('hidden')")
    c.eval("document.querySelector('#agree').checked=true; document.querySelector('#consent-btn').click(); true")
    wait("document.querySelector('#consent').classList.contains('hidden')")
    c.eval("document.querySelector('[data-tab=chat]').click(); true")
    wait("document.querySelector('#chat-input') !== null")
    c.eval("document.querySelector('#chat-input').value='浏览器联调：取餐口可能拥堵，如何开始分析？'; document.querySelector('#send-chat').click(); true")
    wait("document.querySelectorAll('#chat-messages .bubble.assistant').length >= 1",120)
    assert c.eval("document.querySelector('#chat-messages .bubble.assistant').textContent.length")>10
    before=c.eval("document.querySelectorAll('#chat-messages .bubble').length")
    shot=c.send('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False})['data']
    Path('/private/tmp/cps-chat.png').write_bytes(base64.b64decode(shot))
    c.send('Page.reload',{'ignoreCache':True})
    wait("!document.querySelector('#student').classList.contains('hidden')")
    c.eval("document.querySelector('[data-tab=chat]').click(); true")
    wait(f"document.querySelectorAll('#chat-messages .bubble').length >= {before}")
    assert c.eval("document.querySelector('#chat-messages').textContent.includes('浏览器联调')")
    print('PASS: browser login, consent, chat reply display, reload and conversation recovery; screenshot /private/tmp/cps-chat.png')
    