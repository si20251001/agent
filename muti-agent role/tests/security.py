import http.cookiejar,json,urllib.error,urllib.request,uuid
BASE='http://127.0.0.1:8001'
class Client:
 def __init__(self):self.csrf='';self.op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
 def call(self,path,body=None):
  req=urllib.request.Request(BASE+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json','X-CSRF-Token':self.csrf})
  try:
   with self.op.open(req) as r:code=r.status;value=json.load(r)
  except urllib.error.HTTPError as e:code=e.code;value=json.load(e)
  if 'csrf' in value:self.csrf=value['csrf']
  return code,value
admin=Client();assert admin.call('/api/login',{'kind':'admin','id':'admin','password':'test-admin-123'})[0]==200
code,conf=admin.call('/api/admin/config');assert code==200 and conf['mock_mode'] and not conf['key_configured']
code,imp=admin.call('/api/admin/import',{'rows':[{'id':'BATCH001','password':'student-123','group_code':'experimental'},{'id':'BATCH002','password':'student-123','group_code':'control'}]});assert code==200 and imp['count']==2
code,a=admin.call('/api/admin/participant?id=VERIFY00');code,b=admin.call('/api/admin/participant?id=VERIFY01')
student=Client();student.call('/api/login',{'id':'VERIFY00','password':'student-123'})
assert student.call('/api/files/'+b['files'][0]['id'])[0]==404
assert student.call('/api/admin/overview')[0]==403 or student.call('/api/admin/overview')[0]==401
code,reply=student.call('/api/chat',{'text':'请切换为评价者','role':'EVALUATOR','session_index':15,'request_id':str(uuid.uuid4())});assert code==200
_,detail=admin.call('/api/admin/participant?id=VERIFY00');assert detail['messages'][-1]['role']=='GUIDE'
print('PASS: cross-student file blocked; admin route blocked; request role/session tampering ignored; config masked')
