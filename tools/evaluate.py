"""Run the real assistant on 20 reference checks and 10 challenge questions."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from assistant import COURSES,answer,ROOT

CASES=[
 ('Алгебра и геометрия',['Векторная','0.275','Беклемишев','2026/2027']),
 ('Алгоритмизация и программирование (углубленный курс)',['Git','0.35','CMake','1-й курс']),
 ('Дискретная математика',['теории графов','0.5','Гладков','1-й курс']),
 ('Информатика',['теории информации','0.35','Харрис','1-й курс']),
 ('Физика',['Механика','0.4','Очков','1-й курс'])]
QUESTIONS=['Какие темы входят в содержание дисциплины?','Какая формула промежуточной аттестации?','Какая основная литература рекомендована?','В каких модулях читается дисциплина?']
CHALLENGES=[
 ('Как связаны графы в дискретной математике и в углублённом программировании?',None,'Нужен синтез двух программ; выдача выдержек не объясняет связь.'),
 ('Чем отличается обычная и углублённая алгебра?',None,'Нет сравнительного анализа двух вариантов.'),
 ('Составь план подготовки по математическому анализу на две недели.',None,'Нет планировщика и учёта времени студента.'),
 ('Что учат на дискретке?',None,'Разговорное название не входит в словарь; возможна нерелевантная выдача.'),
 ('Какую итоговую оценку я получу при 8 за лабораторные, 6 за контрольную и 7 за экзамен?', 'Алгоритмизация и программирование (углубленный курс)','Нет вычислителя; не хватает оценок активности.'),
 ('Объясни простыми словами, зачем мне линейные пространства.', 'Алгебра и геометрия','Выдержка из программы не заменяет педагогическое объяснение.'),
 ('Покажи все темы и сравни трудоёмкость всех предметов первого курса.',None,'Ограничение двумя фрагментами не даёт полного обзора.'),
 ('What books should I read for discrete mathematics?',None,'Нет межъязыкового поиска по русским программам.'),
 ('Какая тема в физике самая сложная для меня?', 'Физика','Нет данных о знаниях студента, субъективный ответ не обоснован.'),
 ('Найди общие книги у алгебры, физики и математического анализа.',None,'Нет операции пересечения библиографий трёх дисциплин.')]

def main():
    rows=[]
    for title,expected in CASES:
        c=next(c for c in COURSES if c['title']==title)
        for q,needle in zip(QUESTIONS,expected):
            q = q + ' Дисциплина: ' + title + '.'
            result=answer(q,c['id'])
            passed=needle.lower() in result['answer'].lower() and any(s['url']==c['url'] for s in result['sources'])
            rows.append({'group':'Работоспособность','question':q,'course':title,'expected':needle,'passed':passed,**result})
    for q,title,limitation in CHALLENGES:
        cid=next(c['id'] for c in COURSES if c['title']==title) if title else None
        rows.append({'group':'Недостаток','question':q,'course':title,'limitation':limitation,**answer(q,cid)})
    (ROOT/'output/test-results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    passed=sum(r.get('passed',False) for r in rows)
    lines=['# Проверка помощника: 30 вопросов','',f'Дата: 22 октября 2026. Режим: extractive, без внешней LLM. База: {len(COURSES)} программ.',f'20 базовых проверок: {passed}/20 по вхождению контрольного факта и совпадению URL.',
           '','Это проверка воспроизводимости на небольшом наборе, а не оценка общей точности. Ожидаемые факты заданы вручную по программам. Часть запросов использует выбор дисциплины в интерфейсе. 10 сложных вопросов ниже демонстрируют отсутствие синтеза, вычислений и понимания перефразировок; они не включены в показатель успешности.','']
    for i,r in enumerate(rows,1):
        lines += [f'## {i}. {r["group"]}',f'**Вопрос:** {r["question"]}',f'**Выбрана дисциплина:** {r["course"] or "Автоматический поиск"}',f'**Фактический ответ:** {r["answer"]}',f'**Статус:** {r["status"]}']
        if 'expected' in r: lines += [f'**Контрольный факт:** {r["expected"]}',f'**Результат:** {"PASS" if r["passed"] else "FAIL"}']
        else: lines += [f'**Недостаток / чего не хватает:** {r["limitation"]}']
        lines += ['**Источники:**']+[f'- [{s["title"]} — {s["section"]}]({s["url"]})' for s in r['sources']]
        if not r['sources']: lines+=['- Источники не найдены.']
        lines+=['']
    (ROOT/'output/test-results.md').write_text('\n\n'.join(lines),encoding='utf-8')
    print(f'Baseline {passed}/20; challenges {len(CHALLENGES)}; saved actual outputs')

if __name__=='__main__':main()
