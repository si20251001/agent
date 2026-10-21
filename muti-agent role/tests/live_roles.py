"""Advance the browser smoke participant naturally to S11, using real AI at S6/S11."""
import base64, http.cookiejar, json, os, sys, urllib.error, urllib.request, uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['DATA_DIR']='/private/tmp/cps-live-site'
import server
BASE='http://127.0.0.1:8001'
class Client:
 def __init__(self):self.op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()));self.csrf=''
 def call(self,path,body=None,expected=200):
  req=urllib.request.Request(BASE+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json','X-CSRF-Token':self.csrf})
  try:
   with self.op.open(req,timeout=180) as r:code=r.status;value=json.load(r)
  except urllib.error.HTTPError as e:code=e.code;value=json.load(e)
  assert code==expected,(path,code,value)
  if 'csrf' in value:self.csrf=value['csrf']
  return value

def login():
 c=Client();c.call('/api/login',{'id':'BROWSER01','password':'student-123'});return c
c=login()
for idx in range(1,12):
 state=c.call('/api/state');assert state['active_session']==idx,(idx,state['active_session'])
 if idx in (6,11):
  text='我提出了在取餐口增加提示信息的想法，但还没有验证它能否帮助学生。请根据我目前的想法给出适合本次任务的帮助。'
  r=c.call('/api/chat',{'text':text,'request_id':str(uuid.uuid4()),'role':'GUIDE','session_index':1})
  assert len(r['reply'])>20 and '无法可靠核验' not in r['reply']
  print(f'S{idx} real response displayed by API; length={len(r["reply"])}',flush=True)
 if state['survey_status'] and state['survey_status']!='submitted':
  q=c.call('/api/survey');answers={x['id']:('A' if x['scale']=='single_choice' else '50' if x['scale']=='tlx100' else '3') for x in q['items']}
  c.call('/api/survey/submit',{'answers':answers})
 if idx in (5,10):
  pdf=base64.b64encode(b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF').decode()
  fid=c.call('/api/upload',{'filename':f'live-S{idx}.pdf','data':pdf})['id']
  c.call('/api/deliverable',{'file_id':fid})
 c.call('/api/close',{})
 if idx in (5,10):
  c=login()
  assert len(c.call('/api/messages?session=1')['messages'])==2

db=server.connect()
rows=list(db.execute("SELECT session_index,role,model,prompt_hash,status,safety_result FROM messages WHERE participant_id='BROWSER01' AND speaker='assistant' ORDER BY session_index"))
assert [r['session_index'] for r in rows]==[1,6,11]
assert [r['role'] for r in rows]==['GUIDE','COACH','EVALUATOR']
assert all(r['model']=='deepseek-flash' and r['status']=='complete' for r in rows)
assert all(json.loads(r['safety_result'])['passed'] for r in rows)
for r in rows:
 key=r['role'].lower();assert r['prompt_hash']==server.PROMPT_HASH['base']+':'+server.PROMPT_HASH[key]
print('PASS: real DeepSeek GUIDE -> COACH -> EVALUATOR; role-specific prompt hashes; reviewer passed; relogin restored chat',flush=True)
