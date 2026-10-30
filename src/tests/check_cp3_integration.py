"""CP3 integration v1.0: published encodings and counts versus preserved ELF."""
import importlib.util
import json
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[2]

def main():
    report = (ROOT/'report/CP3.md').read_text(encoding='utf-8')
    attachment = (ROOT/'instructions/02_MIN/report/自訂指令格式與機器碼.md').read_text(encoding='utf-8')
    for rel in ['README.md','CONTRIBUTIONS.md','report/CP3.md','report/README.md','instructions/MIN/README.md','instructions/02_MIN/report/自訂指令格式與機器碼.md']:
        assert not re.search(r'^(<<<<<<<|=======|>>>>>>>)', (ROOT/rel).read_text(encoding='utf-8'), re.M), rel
    rows = re.findall(r'\| min x(\d+),x(\d+),x(\d+) \| ([01 ]+) \| (0x[0-9A-F]+) \|',report)
    assert len(rows)==3
    for rd,rs1,rs2,bits,word in rows:
        expected=(0,int(rs2),int(rs1),0,int(rd),11)
        w=int(word,16)
        decoded=((w>>25)&127,(w>>20)&31,(w>>15)&31,(w>>12)&7,(w>>7)&31,w&127)
        assert decoded==expected and int(bits.replace(' ',''),2)==w
        assert word in attachment
        reverse='| '+word+' | '+' | '.join(map(str,expected))+' |'
        assert reverse in attachment
    assert '31:25' in attachment and '32:25' not in attachment and '0x0118178B' not in attachment
    print('Published binary/hex/register fields and reverse decoding: 3/3 PASS')
    spec=importlib.util.spec_from_file_location('cp3_semantics',ROOT/'src/tests/check_cp3_semantics.py')
    sem=importlib.util.module_from_spec(spec);spec.loader.exec_module(sem)
    spec=importlib.util.spec_from_file_location('cp3_baseline',ROOT/'src/tests/check_cp2.py')
    base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
    evidence=ROOT/'src/references/validation/2026-10-23-gcc15/gcc_run_fixed'
    metrics=json.loads((evidence/'measurements.json').read_text(encoding='utf-8-sig'))
    elf=base.ELF32(evidence/'min_rv32im.elf')
    source=(ROOT/'src/tests/test_min.c').read_text(encoding='utf-8-sig')
    cases=[tuple(sem.parse_number(v) for v in row) for row in re.findall(r'\{"[^"]*",\s*([^,]+),\s*([^,]+),\s*([^}]+)\}',source)]
    for label,symbol in [('C baseline（編譯後 min_s32）','min_s32'),('Branch（min_branch）','min_branch'),('Branchless（min_branchless）','min_branchless')]:
        saved=metrics['routines'][symbol]
        static=elf.static_metrics(symbol)['instructions']
        traces=[base.run_function(elf,symbol,a,b) for a,b,_ in cases]
        assert all(t['result']==e for t,(_,_,e) in zip(traces,cases))
        dynamic=sum(t['instructions'] for t in traces)
        branches=sum(t['conditional_branches'] for t in traces)
        assert static==saved['static']['instructions'] and dynamic==saved['dynamic_cp1_14']['instructions']
        expected=f'| {label} | {static-1} | {static} | {dynamic-14} | {dynamic} | {branches} |'
        assert expected in report, expected
    assert '| 自訂 MIN | 1 | 2 | 14 | 28 | 0 | 設計預期' in report
    print('C/Branch/Branchless: original 14 cases each + published count table: 42/42 PASS')
    print('Custom counts: design expectation only; no custom opcode execution or cycles')

if __name__=='__main__':
    main()
