import hashlib,json,unittest
from assistant import COURSES,ROOT,answer

class AssistantTests(unittest.TestCase):
    def test_corpus_provenance(self):
        self.assertEqual(len(COURSES),25)
        for c in COURSES:
            self.assertEqual(c['year'],'2026/2027')
            self.assertEqual(hashlib.sha256((ROOT/'data/raw'/f'{c["id"]}.html').read_bytes()).hexdigest(),c['sha256'])
            meta=c['sections'][0]['text']
            self.assertIn('2026/2027',meta)
            self.assertIn('1-й курс',meta)
            for s in c['sections']:
                if 'аттестация' in s['section']: self.assertNotIn('2027/2028',s['text'])
    def test_formula_preserved(self):
        c=next(c for c in COURSES if c['title']=='Алгоритмизация и программирование (углубленный курс)')
        r=answer('Какая формула оценивания?',c['id'])
        self.assertIn('0.35 * Лабораторные работы 1',r['answer'])
        self.assertEqual(r['sources'][0]['section'],'Промежуточная аттестация')
    def test_scope_and_invalid_input(self):
        self.assertEqual(answer('')['status'],'clarify')
        self.assertEqual(answer('Что на 3 курсе?')['status'],'out_of_scope')
        self.assertEqual(answer('Какие темы?','nonexistent')['status'],'clarify')
    def test_sources_are_official(self):
        for c in COURSES:
            r=answer('Какие темы изучают?',c['id'])
            for s in r['sources']: self.assertEqual(s['url'],c['url'])

if __name__=='__main__':unittest.main()
