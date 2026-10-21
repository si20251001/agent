"""Check two real-model students remain isolated after relogin."""
import http.cookiejar,json,urllib.error,urllib.request,uuid
BASE='http://127.0.0.1:8001'
class C:
 def __init__(self):self.o=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()));self.csrf=''
 def call(self,p,b=None,expect=200):
  req=urllib.request.Request(BASE+p,data=json.dumps(b).encode() if b is not None else None,headers={'Content-Type':'application/json','X-CSRF-Token':self.csrf})
  try:
   with self.o.open(req,timeout=180) as r:status=r.status;v=json.load(r)
  except urllib.error.HTTPError as e:status=e.code;v=json.load(e)
  assert status==expect,(p,status,v)
  if 'csrf' in v:self.csrf=v['csrf']
  return v
admin=C();admin.call('/api/login',{'kind':'admin','id':'admin','password':'test-admin-123'})
admin.call('/api/admin/create',{'id':'BROWSER02','password':'student-123','group_code':'experimental'})
student=C();student.call('/api/login',{'id':'BROWSER02','password':'student-123'});student.call('/api/consent',{'agree':True})
text='我是第二位被试，我想分析点餐与取餐之间的信息衔接。'
reply=student.call('/api/chat',{'text':text,'request_id':str(uuid.uuid4())})['reply'];assert len(reply)>20
own=student.call('/api/messages?session=1')['messages'];assert len(own)==2 and text==own[0]['content']
student=C();student.call('/api/login',{'id':'BROWSER02','password':'student-123'})
restored=student.call('/api/messages?session=1')['messages'];assert restored==own
first=admin.call('/api/admin/participant?id=BROWSER01');second=admin.call('/api/admin/participant?id=BROWSER02')
assert len(first['messages'])==6 and len(second['messages'])==2
assert all('第二位被试' not in m['content'] for m in first['messages'])
assert all('浏览器联调' not in m['content'] for m in second['messages'])
assert second['messages'][-1]['model']=='deepseek-flash' and json.loads(second['messages'][-1]['safety_result'])['passed']
print('PASS: two real-model participants isolated; second participant relogin restored its own chat')
