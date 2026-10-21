from pathlib import Path
import json, re
root=Path(__file__).parent
for source,target in [('01_base_identity.md','base'),('02_guide.md','guide'),('03_coach.md','coach'),('04_evaluator.md','evaluator')]:
    s=(root/source).read_text()
    if target=='base': s=s.split('## 9. 全局Prompt文本')[1]
    elif target=='guide': s=s.split('## 7. 可直接加载的生产Prompt')[1]
    elif target=='coach': s=s.split('## 7. 可直接装载的阶段Prompt')[1]
    else: s=s.split('## 7. 可直接装载的阶段Prompt')[1]
    prompt=s.split('```text',1)[1].split('```',1)[0].strip()+'\n'
    (root/'runtime_prompts'/f'{target}.txt').write_text(prompt)

spec=(root/'08_survey_implementation_spec.md').read_text()
items=[]
section=''
for line in spec.splitlines():
    if line.startswith('### '): section=line[4:].strip()
    if not line.startswith('| `'): continue
    cols=[c.strip() for c in line.strip().strip('|').split('|')]
    qid=cols[0].strip('`')
    if not re.fullmatch(r'(?:CSE|PS|TLX|CT|RU|CU|TU|PL|CM|EV|IG|MC|FE)\d+|W[123]-[AB]\d+',qid): continue
    if qid.startswith('PS') or qid.startswith('W'):
        text=cols[2]
        label=cols[1]
    else:
        text=cols[1]
        label=''
    typ='tlx100' if qid.startswith('TLX') else 'likert7' if qid.startswith(('PS','CT')) else 'frequency5' if qid.startswith(('RU','CU','TU')) else 'likert5'
    items.append({'id':qid,'text':text,'label':label,'scale':typ,'section':section})
items.append({'id':'ROLE','text':'回顾本周与AI服务设计专家的交流，你认为它主要以哪种方式帮助你完成创新任务？','label':'','scale':'single_choice','section':'AI角色识别','choices':{'A':'方法指导：主要解释知识、提供示例或分步骤说明如何开展任务','B':'思考引导：主要通过提问，促使我检查思路、解释理由并自主作出判断','C':'方案评价：主要评价我已经完成的内容、指出不足，并引导我自主修订','D':'多种方式并重：没有哪一种方式明显占主导','E':'无法判断：本周的互动不足以判断其主要支持方式'}})
assert len(items)==92,len(items)
(root/'survey_questions.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')
