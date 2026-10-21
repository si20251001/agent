"""Synthetic participant checks real DeepSeek through the website HTTP backend."""
import http.cookiejar,json,urllib.error,urllib.request,uuid
BASE='http://127.0.0.1:8001'
class Client:
 def __init__(self):self.op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()));self.csrf=''
 def call(self,path,body=None):
  req=urllib.request.Request(BASE+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json','X-CSRF-Token':self.csrf})
  with self.op.open(req,timeout=180) as r:value=json.load(r)
  if 'csrf' in value:self.csrf=value['csrf']
  return value
admin=Client();admin.call('/api/login',{'kind':'admin','id':'admin','password':'test-admin-123'})
config=admin.call('/api/admin/config');assert config['key_configured'] and config['model']=='deepseek-flash' and not config['mock_mode']
admin.call('/api/admin/create',{'id':'REALHTTP01','password':'student-123','group_code':'experimental'})
student=Client();student.call('/api/login',{'id':'REALHTTP01','password':'student-123'});student.call('/api/consent',{'agree':True})
message='我想分析取餐口排队，但目前只有个人观察。应该怎样开始？'
answer=student.call('/api/chat',{'text':message,'request_id':str(uuid.uuid4())})
assert len(answer['reply'])>20 and '无法可靠核验' not in answer['reply']
student=Client();student.call('/api/login',{'id':'REALHTTP01','password':'student-123'})
history=student.call('/api/messages?session=1')['messages'];assert len(history)==2 and history[0]['content']==message and history[1]['content']==answer['reply']
detail=admin.call('/api/admin/participant?id=REALHTTP01')
assistant=detail['messages'][-1];verdict=json.loads(assistant['safety_result'])
assert assistant['role']=='GUIDE' and assistant['model']=='deepseek-flash' and verdict['passed']
assert assistant['status']=='complete' and assistant['prompt_hash']
print('PASS: private config loaded; real DeepSeek HTTP chat returned, reviewed, stored, and restored after relogin')
print('response_length:',len(answer['reply']))
