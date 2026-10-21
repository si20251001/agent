"""Copy a shell-held API key to a private local backend config; never prints it."""
import json, os, stat, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
DEST=DATA/'private_config.json'
key=os.environ.get('LLM_API_KEY','')
if not key:
    raise SystemExit('当前终端无法读取 LLM_API_KEY；请在设置该变量的终端运行。')
config={
    'LLM_API_KEY':key,
    'LLM_BASE_URL':os.environ.get('LLM_BASE_URL','https://api.deepseek.com/v1'),
    'LLM_MODEL':os.environ.get('LLM_MODEL','deepseek-flash'),
    'LLM_THINKING':os.environ.get('LLM_THINKING','disabled'),
}
DATA.mkdir(parents=True,exist_ok=True)
fd,tmp=tempfile.mkstemp(prefix='.private_config_',dir=DATA)
try:
    os.fchmod(fd,stat.S_IRUSR|stat.S_IWUSR)
    with os.fdopen(fd,'w') as out:json.dump(config,out,ensure_ascii=False)
    os.replace(tmp,DEST)
except Exception:
    try:os.unlink(tmp)
    except FileNotFoundError:pass
    raise
print('已保存本机后端配置：',DEST)
print('文件权限：0600；API Key 未输出。')
