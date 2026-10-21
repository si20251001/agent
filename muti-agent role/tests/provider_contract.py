import json, os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
os.environ.update(LLM_API_KEY='test-only-placeholder',LLM_BASE_URL='https://api.deepseek.com/v1',LLM_MODEL='deepseek-flash',LLM_THINKING='disabled')
class Reply:
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def read(self):return b'{"choices":[{"message":{"content":"ok"}}]}'
seen=[]
def fake_open(request,timeout=0):
    seen.append((request.full_url,json.loads(request.data)))
    return Reply()
server.urllib.request.urlopen=fake_open
assert server.llm_call([{'role':'user','content':'hello'}])=='ok'
url,body=seen[0]
assert url=='https://api.deepseek.com/v1/chat/completions'
assert body['model']=='deepseek-flash' and body['thinking']=={'type':'disabled'}
assert body['temperature']==0.4
print('PASS: DeepSeek endpoint, model, disabled thinking, fixed temperature')
