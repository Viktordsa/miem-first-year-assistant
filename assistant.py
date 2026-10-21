"""Offline, evidence-only retrieval assistant. Python 3.10+, no runtime dependencies."""
import json, math, re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COURSES = json.loads((ROOT/'data/courses.json').read_text(encoding='utf-8'))
STOP = set('какие какой какая как что где когда ли и в на по из для у с о об это курса курсе дисциплины расскажи пожалуйста'.split())

def tokens(s):
    return [w[:7] if len(w)>7 else w for w in re.findall(r'[а-яёa-z0-9]+',s.lower().replace('ё','е')) if w not in STOP]

def intent(q):
    q=q.lower()
    for keys, section in [(['литератур','книг','учебник'],'литератур'),(['формул','итогов','аттеста'],'аттестация'),(['оцен','балл','контрол'],'оцен'),(['кредит','модул','язык','преподавател','кто читает'],'паспорт'),(['тем','содержан','изуч','проход'],'содержание'),(['цел'],'цель')]:
        if any(k in q for k in keys): return section
    return None

def answer(question, course_id=None):
    q=question.strip()
    if not q: return {'answer':'Введите вопрос.','sources':[],'status':'clarify'}
    if len(q)>2000: return {'answer':'Сократите вопрос до 2000 символов.','sources':[],'status':'clarify'}
    if re.search(r'202[0-5]|202[89]|203\d|[2-4][ -]?(?:й )?курс',q):
        return {'answer':'База ограничена первым курсом ИВТ МИЭМ за 2026/2027 год.','sources':[],'status':'out_of_scope'}
    selected=[c for c in COURSES if c['id']==course_id] if course_id else []
    if course_id and not selected: return {'answer':'Дисциплина не найдена.','sources':[],'status':'clarify'}
    if not selected:
        matches=[c for c in COURSES if c['title'].lower() in q.lower()]
        if matches:
            maxlen=max(len(c['title']) for c in matches)
            selected=[c for c in matches if len(c['title'])==maxlen]
        else:
            qt=set(tokens(q)); scored=sorted([(len(qt&set(tokens(c['title'])))/max(1,len(set(tokens(c['title'])))),c['id'],c) for c in COURSES],reverse=True)
            if scored[0][0]>=.65: selected=[x[2] for x in scored if x[0]==scored[0][0]]
    if len(selected)>1:
        return {'answer':'Уточните вариант дисциплины: '+ '; '.join(c['title'] for c in selected), 'sources':[],'status':'clarify'}
    pool=selected or COURSES
    target=intent(q)
    sections=[]
    for c in pool:
        for s in c['sections']:
            name=s['section'].lower()
            if target=='литератур' and 'основн' in q.lower() and 'основн' not in name: continue
            if target and not (target in name or (target=='оцен' and ('контрол' in name or 'assessment' in name))): continue
            for offset in range(0,len(s['text']),1000):
                # Fixed windows overlap to avoid losing text at boundaries.
                text=s['text'][max(0,offset-120):offset+1000]
                sections.append((c,s['section'],text))
    if not sections:
        return {'answer':'В загруженной программе этот раздел не найден. Проверьте полную программу по ссылке.','sources':[{'title':c['title'],'url':c['url'],'section':'Программа'} for c in selected],'status':'not_found'}
    qt=set(tokens(q)); df=Counter(t for _,_,txt in sections for t in set(tokens(txt)))
    ranked=[]
    for c,sec,txt in sections:
        ts=Counter(tokens(txt)); overlap=qt & ts.keys()
        score=sum((1+math.log((len(sections)+1)/(df[t]+1)))*ts[t]/(ts[t]+1) for t in overlap)
        if selected and target: score+=2
        ranked.append((score,c['id'],sec,txt,c))
    ranked.sort(key=lambda x:x[0],reverse=True)
    if ranked[0][0]<1.1:
        return {'answer':'В программах не найдено достаточно данных для ответа. Уточните дисциплину или формулировку.','sources':[],'status':'not_found'}
    best=ranked[:2] if not selected else ranked[:1]
    passages=[]; sources=[]
    for _,_,sec,txt,c in best:
        # Extract sentences/entries rather than inventing a generative summary.
        pattern = r'\s*\|\s*' if target else r'\s*\|\s*|(?<=[.!?])\s+(?=[А-ЯA-Z])'
        parts=[p.strip() for p in re.split(pattern,txt) if p.strip()]
        if target=='паспорт': chosen=parts
        elif target in ('содержание','литератур','оцен','аттестация'): chosen=parts[:8]
        else:
            chosen=sorted(parts,key=lambda p:len(qt&set(tokens(p))),reverse=True)[:3]
        excerpt='; '.join(chosen)
        if len(excerpt)>850: excerpt=excerpt[:850].rsplit(' ',1)[0]+'…'
        passages.append(f'{c["title"]} — {sec}: {excerpt} [{len(sources)+1}]')
        sources.append({'title':c['title'],'url':c['url'],'section':sec,'evidence':txt})
    return {'answer':'По программе: '+ '\n\n'.join(passages),'sources':sources,'status':'found','mode':'extractive','note':'Это краткая выдержка. Для полной формулы и условий откройте источник.'}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('question'); p.add_argument('--course'); a=p.parse_args()
    print(json.dumps(answer(a.question,a.course),ensure_ascii=False,indent=2))
