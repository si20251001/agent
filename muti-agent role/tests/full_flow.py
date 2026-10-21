"""Complete S1-S15 for two isolated mock participants over the HTTP API."""
import base64, http.cookiejar, json, os, urllib.error, urllib.request, uuid
BASE=os.environ.get('TEST_URL','http://127.0.0.1:8001')
class Client:
 def __init__(self):self.jar=http.cookiejar.CookieJar();self.op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar));self.csrf=''
 def call(self,path,body=None,expected=200):
  req=urllib.request.Request(BASE+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json','X-CSRF-Token':self.csrf})
  try:
   with self.op.open(req,timeout=70) as r:status=r.status;value=json.load(r)
  except urllib.error.HTTPError as e:status=e.code;value=json.load(e)
  assert status==expected,(path,status,value)
  if 'csrf' in value:self.csrf=value['csrf']
  return value

def make_admin():
 a=Client();a.call('/api/login',{'kind':'admin','id':'admin','password':'test-admin-123'});return a
admin=make_admin()
for pid,group in [('FLOWEXP','experimental'),('FLOWCTL','control')]:
 admin.call('/api/admin/create',{'id':pid,'password':'student-123','group_code':group})

def participant(pid):
 c=Client();c.call('/api/login',{'id':pid,'password':'student-123'});c.call('/api/consent',{'agree':True})
 uploaded=[]
 for idx in range(1,16):
  state=c.call('/api/state');assert state['active_session']==idx and state['task']['index']==idx
  question=f'{pid} 在 S{idx} 的想法与证据应该如何核对？'
  c.call('/api/chat',{'text':question,'request_id':str(uuid.uuid4()),'role':'GUIDE' if idx>5 else 'EVALUATOR','session_index':15})
  messages=c.call('/api/messages?session='+str(idx))['messages'];assert len(messages)==2 and question in messages[0]['content']
  if state['survey_status']:
   q=c.call('/api/survey');count={2:16,4:16,5:56,6:16,8:16,10:73,12:16,14:16,15:57}[idx]
   assert len(q['items'])==count,(idx,len(q['items']))
   answers={x['id']:('A' if x['scale']=='single_choice' else '50' if x['scale']=='tlx100' else '3') for x in q['items']}
   c.call('/api/survey/draft',{'answers':dict(list(answers.items())[:2])})
   c.call('/api/survey/submit',{'answers':answers})
   c.call('/api/survey/submit',{'answers':answers},409)
  if idx in (5,10,15):
   c.call('/api/close',{},409)
   pdf=base64.b64encode(b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF').decode()
   file=c.call('/api/upload',{'filename':f'{pid}-S{idx}.pdf','data':pdf})
   uploaded.append(file['id'])
   c.call('/api/deliverable',{'file_id':file['id']})
  c.call('/api/close',{})
  if idx in (5,10):
   c=Client();c.call('/api/login',{'id':pid,'password':'student-123'})
   old=c.call('/api/messages?session=1')['messages'];assert len(old)==2 and pid in old[0]['content']
 assert c.call('/api/state')['active_session']==16
 return uploaded
files_exp=participant('FLOWEXP');files_ctl=participant('FLOWCTL')
student=Client();student.call('/api/login',{'id':'FLOWEXP','password':'student-123'});student.call('/api/files/'+files_ctl[0],expected=404)
for pid,group in [('FLOWEXP','experimental'),('FLOWCTL','control')]:
 p=admin.call('/api/admin/participant?id='+pid)
 assert len(p['messages'])==30 and len(p['deliverables'])==3 and len(p['surveys'])==9
 roles={m['session_index']:m['role'] for m in p['messages'] if m['speaker']=='assistant'}
 assert roles[5]=='GUIDE' and roles[6]==('COACH' if group=='experimental' else 'GUIDE')
 assert roles[10]==('COACH' if group=='experimental' else 'GUIDE')
 assert roles[11]==('EVALUATOR' if group=='experimental' else 'GUIDE')
 assert roles[15]==('EVALUATOR' if group=='experimental' else 'GUIDE')
 assert all(m['status']=='complete' for m in p['messages'])
print('PASS: S1-S15 experimental/control; 3 role stages; 30 isolated chat messages each; relogin restoration; all surveys; 3 deliverables; final gate')
