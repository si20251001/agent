"""Verify completed participants can browse earlier chats in the actual UI."""
import base64, os, time
from pathlib import Path
os.environ['BROWSER_DATA_DIR']='/private/tmp/cps-live-site'
from browser_flow import CDP,target
c=CDP(target()['webSocketDebuggerUrl'])
def wait(expression,seconds=15):
 start=time.time()
 while time.time()-start<seconds:
  try:
   if c.eval(expression):return
  except Exception:pass
  time.sleep(.2)
 raise AssertionError('Timed out: '+expression)
c.send('Page.reload',{'ignoreCache':True})
wait("document.querySelector('#student') && !document.querySelector('#student').classList.contains('hidden')")
c.eval("document.querySelector('[data-tab=chat]').click(); true")
wait("document.querySelector('#chat-session-select') !== null")
assert c.eval("document.querySelector('#chat-session-select').options.length")==15
for idx in (1,6,11):
 c.eval(f"var select=document.querySelector('#chat-session-select'); select.value='{idx}'; select.dispatchEvent(new Event('change')); true")
 wait(f"document.querySelector('#chat-session-select').value==='{idx}' && document.querySelectorAll('#chat-messages .bubble').length===2")
 assert c.eval("document.querySelector('#chat-input')===null")
 assert c.eval("document.querySelector('#chat-messages .bubble.assistant').textContent.length>20")
c.eval("var select=document.querySelector('#chat-session-select'); select.value='1'; select.dispatchEvent(new Event('change')); true")
wait("document.querySelector('#chat-messages .bubble.assistant') !== null")
assert c.eval("document.querySelector('#chat-messages .bubble.assistant strong') !== null")
assert c.eval("document.querySelector('#chat-messages .bubble.assistant table') !== null")
shot=c.send('Page.captureScreenshot',{'format':'png'})['data']
Path('/private/tmp/cps-archive.png').write_bytes(base64.b64decode(shot))
print('PASS: completed participant can view S1/S6/S11 history in browser; archived chat is read-only; Markdown formatted')
