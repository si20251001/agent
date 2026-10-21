import concurrent.futures, http.cookiejar, json, os, sys, urllib.error, urllib.request, uuid, base64
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
import server
BASE=os.environ.get('TEST_URL','http://127.0.0.1:8001')
class Client:
 def __init__(self):self.jar=http.cookiejar.CookieJar();self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar));self.csrf=''
 def call(self,path,data=None):
  headers={'Content-Type':'application/json'}
  if self.csrf:headers['X-CSRF-Token']=self.csrf
  req=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
  try:
   with self.opener.open(req,timeout=70) as r: result=json.loads(r.read())
  except urllib.error.HTTPError as e:raise AssertionError((path,e.code,e.read().decode()))
  if 'csrf' in result:self.csrf=result['csrf']
  return result
admin=Client();admin.call('/api/login',{'kind':'admin','id':'admin','password':'test-admin-123'})
for i in range(10):
 pid=f'VERIFY{i:02d}'
 try:admin.call('/api/admin/create',{'id':pid,'password':'student-123','group_code':'experimental' if i<9 else 'control'})
 except AssertionError as e:
  if 'UNIQUE constraint' not in str(e):raise

def run(i):
 pid=f'VERIFY{i:02d}';c=Client();c.call('/api/login',{'id':pid,'password':'student-123'});s=c.call('/api/state');assert s['participant_id']==pid and s['active_session']==1
 c.call('/api/consent',{'agree':True})
 c.call('/api/workbook',{'module':'M1','content':f'{pid} 独立观察记录'})
 for j in range(3):
  rid=str(uuid.uuid4());r=c.call('/api/chat',{'text':f'{pid} 第{j}轮：请帮我检查流程','request_id':rid});assert r['reply']
  r2=c.call('/api/chat',{'text':'重复请求','request_id':rid});assert r2['duplicate']
 payload=base64.b64encode((pid+' file').encode()).decode();f=c.call('/api/upload',{'filename':pid+'.txt','mime':'text/plain','data':payload})
 s=c.call('/api/state');assert len(s['files'])==1 and s['workbook']['M1']['content'].startswith(pid)
 messages=c.call('/api/messages')['messages'];assert len(messages)==6 and all(pid in m['content'] if m['speaker']=='user' else True for m in messages)
 c.call('/api/close',{});s=c.call('/api/state');assert s['active_session']==2 and s['survey_status']=='pending'
 q=c.call('/api/survey');assert len(q['items'])==16
 answers={x['id']:('50' if x['scale']=='tlx100' else '3') for x in q['items']}
 c.call('/api/survey/draft',{'answers':{'PS1':'7'}});q=c.call('/api/survey');assert q['answers']['PS1']=='7'
 try:c.call('/api/close',{});raise AssertionError('S2 closed without survey')
 except AssertionError as e:assert '请先完成本次问卷' in str(e)
 c.call('/api/survey/submit',{'answers':answers});c.call('/api/close',{})
 assert c.call('/api/state')['active_session']==3
 return pid
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:results=list(pool.map(run,range(10)))
assert len(results)==10
for i in range(10):
 d=admin.call('/api/admin/participant?id=VERIFY%02d'%i)
 assert len(d['messages'])==6 and d['participant']['active_session']==3
 assert len(d['files'])==1 and d['surveys'][0]['status']=='submitted'
 assert {x['scale']:x['mean'] for x in d['scores']}['PS']==round(27/7,4)
print('PASS: 10 students x 3 chats; uploads, workbooks, S2 survey, role/data isolation')
print('PASS survey counts:',[(i,len(server.survey_items(i))) for i in (2,5,10,15)])
print('PASS role map:',[(i,server.role('experimental',i),server.role('control',i)) for i in (5,6,10,11)])
