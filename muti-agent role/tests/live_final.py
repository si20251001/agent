"""Finish S12-S15 on the isolated live-config server without extra model calls."""
import base64, http.cookiejar, json, urllib.error, urllib.request
BASE='http://127.0.0.1:8001'
class C:
 def __init__(self):self.o=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()));self.csrf=''
 def call(self,p,b=None,expect=200):
  req=urllib.request.Request(BASE+p,data=json.dumps(b).encode() if b is not None else None,headers={'Content-Type':'application/json','X-CSRF-Token':self.csrf})
  try:
   with self.o.open(req) as r:code=r.status;v=json.load(r)
  except urllib.error.HTTPError as e:code=e.code;v=json.load(e)
  assert code==expect,(p,code,v)
  if 'csrf' in v:self.csrf=v['csrf']
  return v
c=C();c.call('/api/login',{'id':'BROWSER01','password':'student-123'})
for idx in range(12,16):
 s=c.call('/api/state');assert s['active_session']==idx
 if s['survey_status']:
  q=c.call('/api/survey');a={x['id']:('A' if x['scale']=='single_choice' else '50' if x['scale']=='tlx100' else '3') for x in q['items']};c.call('/api/survey/submit',{'answers':a})
 if idx==15:
  c.call('/api/close',{},409)
  pdf=base64.b64encode(b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF').decode()
  fid=c.call('/api/upload',{'filename':'final-complete.pdf','data':pdf})['id'];c.call('/api/deliverable',{'file_id':fid})
 c.call('/api/close',{})
assert c.call('/api/state')['active_session']==16
admin=C();admin.call('/api/login',{'kind':'admin','id':'admin','password':'test-admin-123'})
d=admin.call('/api/admin/participant?id=BROWSER01')
assert len(d['deliverables'])==3 and len(d['surveys'])==9
assert d['participant']['active_session']==16
print('PASS: S12-S15 surveys, S15 final-file gate, three formal deliverables, completed participant')
