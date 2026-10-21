import base64, json, os, sys, urllib.error, urllib.request, http.cookiejar
BASE=os.environ.get('TEST_URL','http://127.0.0.1:8001')
class C:
 def __init__(self):self.o=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()));self.csrf=''
 def call(self,p,data=None,status=200):
  req=urllib.request.Request(BASE+p,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json','X-CSRF-Token':self.csrf})
  try:
   with self.o.open(req) as r:code=r.status;body=json.load(r)
  except urllib.error.HTTPError as e:code=e.code;body=json.load(e)
  assert code==status,(p,code,body)
  if 'csrf' in body:self.csrf=body['csrf']
  return body
admin=C();admin.call('/api/login',{'kind':'admin','id':'admin','password':'test-admin-123'})
try:admin.call('/api/admin/create',{'id':'WEEKLY1','password':'student-123','group_code':'experimental'})
except AssertionError:pass
c=C();c.call('/api/login',{'id':'WEEKLY1','password':'student-123'});c.call('/api/consent',{'agree':True})
c.call('/api/close',{})
q=c.call('/api/survey');a={x['id']:('50' if x['scale']=='tlx100' else '3') for x in q['items']};c.call('/api/survey/submit',{'answers':a});c.call('/api/close',{})
c.call('/api/close',{})
q=c.call('/api/survey');c.call('/api/survey/submit',{'answers':{x['id']:('50' if x['scale']=='tlx100' else '3') for x in q['items']}});c.call('/api/close',{})
assert c.call('/api/state')['active_session']==5
q=c.call('/api/survey');assert len(q['items'])==56
c.call('/api/close',{},409)
a={x['id']:('A' if x['scale']=='single_choice' else '3') for x in q['items']};c.call('/api/survey/submit',{'answers':a});c.call('/api/close',{},409)
pdf=base64.b64encode(b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF').decode();f=c.call('/api/upload',{'filename':'week1.pdf','data':pdf});c.call('/api/deliverable',{'file_id':f['id']});c.call('/api/close',{})
assert c.call('/api/state')['active_session']==6
p=admin.call('/api/admin/participant?id=WEEKLY1');assert p['sessions'][-1]['role']=='COACH';assert len(p['deliverables'])==1
scores={x['scale']:x['mean'] for x in p['scores'] if x['session_index']==5};assert scores['W1A']==3 and scores['W1B']==3
print('PASS: S5 survey and file gates, versioned deliverable, S6 role transition, weekly scores')
