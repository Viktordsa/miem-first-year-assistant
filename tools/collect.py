"""Download the filtered HSE catalog and preserve verified course pages."""
import json, hashlib, re, time
from pathlib import Path
from urllib.request import Request, urlopen
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
BASE = 'https://www.hse.ru/ba/isct/courses/'

def fetch(url, path):
    if path.exists():
        return path.read_bytes()
    with urlopen(Request(url, headers={'User-Agent': 'MIEM-Student-Assistant/1.0'}), timeout=45) as r:
        b = r.read()
    path.write_bytes(b)
    time.sleep(.35)
    return b

def clean(s):
    return re.sub(r'\s+', ' ', s).strip()

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    links = {}
    for page in (1, 2):
        url = BASE + ('index.html' if page == 1 else 'page2.html') + '?course=1.1.1.4&year=2026'
        tree = html.fromstring(fetch(url, RAW / f'catalog-{page}.html'))
        for item in tree.xpath('//div[contains(concat(" ",@class," ")," edu-events__item ")]'):
            for a in item.xpath('.//div[contains(@class,"edu-events_title")]//a'):
                links[a.get('href')] = clean(a.text_content())
    courses, rejected = [], []
    for url, title in links.items():
        ident = re.search(r'(\d+)\.html', url).group(1)
        b = fetch(url, RAW / f'{ident}.html')
        tree = html.fromstring(b)
        for e in tree.xpath('//script|//style|//nav|//footer'):
            e.drop_tree()
        heads = tree.xpath('//h1')
        header = heads[0].getparent().getparent() if heads else None
        meta = ' | '.join(clean(x) for x in header.itertext() if clean(x)) if header is not None else ''
        meta = meta.split('Программа дисциплины')[0]
        valid = '2026/2027' in meta and bool(re.search(r'1-й курс', meta))
        if not valid:
            rejected.append({'url':url,'title':title,'reason':'year/course not verified'})
            continue
        chunks = []
        for h in tree.xpath('//h4[contains(@class,"section__title")]'):
            nxt = h.getnext()
            if nxt is not None and 'pud__content' in (nxt.get('class') or ''):
                parts = [clean(x) for x in nxt.itertext() if clean(x)]
                section_name=clean(h.text_content())
                if 'аттестация' in section_name or 'Interim Assessment' in section_name:
                    filtered=[]; include=True
                    for part in parts:
                        if re.match(r'20\d\d/20\d\d',part): include=part.startswith('2026/2027')
                        if include: filtered.append(part)
                    parts=filtered
                chunks.append({'section':section_name,'text':' | '.join(parts)})
        chunks.insert(0,{'section':'Паспорт дисциплины','text':meta})
        courses.append({'id':ident,'title':title,'url':url,'year':'2026/2027','course':1,
                        'sha256':hashlib.sha256(b).hexdigest(),'sections':chunks})
    (ROOT/'data/courses.json').write_text(json.dumps(courses,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'data/manifest.json').write_text(json.dumps({'retrieved':'2026-10-22','catalog_urls':[BASE+'?course=1.1.1.4&page=1&year=2026',BASE+'page2.html?course=1.1.1.4&year=2026'],'accepted':len(courses),'rejected':rejected},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Accepted',len(courses),'Rejected',len(rejected))

if __name__=='__main__': main()
