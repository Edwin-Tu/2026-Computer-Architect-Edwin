# MIN CP2 — 完整實驗指南與證據保存

## 0. 適用範圍及來源

本指南從專案根目錄操作，重建的是references/validation/2026-10-23-gcc15/source_snapshot內main@e084ba0的三函式來源。dev min_s32.S及CP1保持不變；不得把快照結果套到dev同名Assembly，也不覆寫任何證據。

以下是可重現操作步驟，不是已成功執行的紀錄。本機缺 RISC-V 工具鏈時必須記為未驗證，不能讀舊統計代替成功。歷史結果見 [CP2 報告](CP2.md)，已保存實際執行分類見 [維護紀錄](CP2_MAINTENANCE.md)。

## 1. 工具、來源及執行條件

需要 Python 3.10 以上、主機 cc/gcc/clang、RISC-V GCC 或支援 RISC-V 的 Clang/LLD；完整反組譯流程另需相符 objdump。指令集固定 `-march=rv32im -mabi=ilp32`。Clang是否支援目標及連結器，以實際命令結果為準；已記錄的CodeBlocks LLVM工具沒有RISC-V target，新建置使用xPack GCC。腳本目前不直接支援 MSVC cl；獨立 MSVC 主機驗證不能冒充腳本的 cc/gcc/clang 流程。

| 來源 | 功能 |
|---|---|
| [min.c](../src/references/validation/2026-10-23-gcc15/source_snapshot/c_baseline/min.c)、[min.h](../src/references/validation/2026-10-23-gcc15/source_snapshot/c_baseline/min.h) | 原有 C baseline／介面 |
| [test_min.c](../src/references/validation/2026-10-23-gcc15/source_snapshot/tests/test_min.c) | 原有14筆輸入、預期答案及主機測試 |
| [min_branch.S](../src/references/validation/2026-10-23-gcc15/source_snapshot/rv32im/min_branch.S) | Branch Assembly |
| [min_branchless.S](../src/references/validation/2026-10-23-gcc15/source_snapshot/rv32im/min_branchless.S) | Branchless Assembly |
| [check_cp2.py](../src/references/validation/2026-10-23-gcc15/source_snapshot/tests/check_cp2.py) | 主機驗證、交叉編譯、ELF讀取及指令計數 |

先確認已在同一個Terminal 設定並 export `PROJECT_COPY` 為目前專案絕對路徑。另須設定 `CP2_RUN_DIR` 為全新且不在證據包內的輸出路徑；可另設定 `HOST_CC`、`RV_CC`、`RV_OBJDUMP`；含空白的工具路徑也須以完整路徑傳入。以下完整 Bash 子程序含必要檔案、工具、狀態與覆寫檢查；任一步驟失敗即結束，不接續讀結果。適用 macOS/Linux Bash；zsh使用者也執行此 Bash 子程序。

## 2. 完整建置、反組譯與保存流程

```bash
bash -euo pipefail <<'CP2_RUN'
set -C
: "${PROJECT_COPY:?請先 export PROJECT_COPY 為目前專案絕對路徑}"
cd "$PROJECT_COPY"
MIN="$PWD/src/references/validation/2026-10-23-gcc15/source_snapshot"
HOST_CC="${HOST_CC:-cc}"
RV_CC="${RV_CC:-riscv64-elf-gcc}"
RV_OBJDUMP="${RV_OBJDUMP:-riscv64-elf-objdump}"
for file in c_baseline/min.c c_baseline/min.h tests/test_min.c rv32im/min_branch.S rv32im/min_branchless.S tests/check_cp2.py; do
  if [ ! -f "$MIN/$file" ]; then
    printf '缺少必要來源：%s\n' "$MIN/$file" >&2
    exit 1
  fi
done
for tool in python3 "$HOST_CC" "$RV_CC" "$RV_OBJDUMP"; do
  if ! command -v "$tool" >/dev/null; then
    printf '缺少必要工具：%s\n' "$tool" >&2
    exit 1
  fi
done
: "${CP2_RUN_DIR:?請指定全新且不在證據目錄內的輸出路徑}"
RUN="$CP2_RUN_DIR"
python3 - "$RUN" "$MIN/.." <<'CHECK_OUTPUT'
import pathlib, sys
output, evidence = (pathlib.Path(x).resolve() for x in sys.argv[1:])
if output == evidence or evidence in output.parents:
    raise SystemExit('拒絕將新輸出寫入保存證據包')
CHECK_OUTPUT
if [ -e "$RUN" ]; then
  printf '拒絕覆寫既有輸出：%s\n' "$RUN" >&2
  exit 1
fi
python3 -B "$MIN/tests/check_cp2.py"   --compiler "$RV_CC" --host-compiler "$HOST_CC"   --source-version "${SOURCE_VERSION:-main@e084ba0-core-unchanged_cp2-validator-v1.2.1}"   --output-dir "$RUN"
python3 - "$RUN" <<'CHECK_STATUS'
import json, pathlib, sys
run = pathlib.Path(sys.argv[1])
s = json.loads((run / 'run_status.json').read_text(encoding='utf-8'))
if s['status'] != 'passed':
    raise SystemExit('完整流程未通過；禁止以略過或失敗結果替代')
for name in ('min_rv32im.elf', 'measurements.json', 'measurements.md'):
    if not (run / name).is_file():
        raise SystemExit('缺少本次產物：' + name)
CHECK_STATUS
"$RV_OBJDUMP" --version > "$RUN/objdump_version.txt"
"$RV_OBJDUMP" -d -M no-aliases "$RUN/min_rv32im.elf" > "$RUN/disassembly.txt"
python3 - "$RUN" <<'SAVE_EVIDENCE'
import datetime, hashlib, json, pathlib, platform, re, sys, zipfile
run = pathlib.Path(sys.argv[1]).resolve()
text = (run / 'disassembly.txt').read_text(encoding='utf-8', errors='replace')
for name in ('min_s32', 'min_branch', 'min_branchless'):
    if not re.search(r'<'+re.escape(name)+r'>:', text):
        raise SystemExit('反組譯缺少函式：'+name)
env = {'date_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'python': sys.version, 'platform': platform.platform(), 'machine': platform.machine(),
       'mac_ver': platform.mac_ver(), 'run': str(run)}
with (run / 'environment_extra.json').open('x', encoding='utf-8') as f:
    json.dump(env, f, ensure_ascii=False, indent=2)
hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(run.iterdir()) if p.is_file()}
with (run / 'artifact_sha256.json').open('x', encoding='utf-8') as f:
    json.dump(hashes, f, ensure_ascii=False, indent=2)
archive = run.with_name(run.name + '.evidence.zip')
with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as z:
    for p in sorted(run.rglob('*')):
        if p.is_file(): z.write(p, p.relative_to(run))
print('本次完整證據目錄：', run)
print('本次完整封存：', archive)
SAVE_EVIDENCE
cat "$RUN/measurements.md"
CP2_RUN
```

`set -C` 避免 shell 重導向覆寫既有反組譯；Python輸出與ZIP用exclusive模式。`--output-dir`必須不存在，腳本才建立它。失敗時留下的run僅供診斷，下次換全新目錄，不刪改失敗紀錄後假裝是同次成功。反組譯或封存失敗表示完整證據流程尚未完成，即使先前run_status已記錄功能測試通過也不能宣稱封存完成。

Windows可用以下PowerShell命令，變數必須使用當前主機的實際路徑。這是需設定前提的操作範例，不是聲稱已執行的紀錄；已成功的原始argv及結果見證據索引。完整反組譯與封存另需相符GNU工具。

```powershell
# 先將這三個變數設為實際工具路徑及不存在的新輸出目錄。
if (-not $RvCompiler -or -not $HostCompiler -or -not $NewRun) { throw '未設定工具或新輸出目錄' }
python -B src/references/validation/2026-10-23-gcc15/source_snapshot/tests/check_cp2.py `
  --compiler "$RvCompiler" --host-compiler "$HostCompiler" `
  --source-version main@e084ba0-core-unchanged_cp2-validator-v1.2.1 --output-dir "$NewRun"
if ($LASTEXITCODE -ne 0) { throw 'CP2未成功；檢查該新run的狀態' }
```

## 3. C編譯、Assembly組譯及連結如何進行

腳本先在全新run以主機編譯器執行下列命令結構（真實完整argv寫於native_build.log）：

```text
cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror
  -I <MIN>/c_baseline <MIN>/c_baseline/min.c <MIN>/tests/test_min.c
  -o <RUN>/native_test_min[.exe]
```

執行產物並同時檢查退出碼、14個PASS列、沒有FAIL及最後 `Result: 14/14 tests passed.`。不是只搜尋一行PASS文字。失敗立即停止。

交叉編譯採以下命令結構；`.S`由GCC driver前處理及組譯，C經編譯，再連結成同一ELF，不修改原始Assembly：

```text
riscv64-elf-gcc -march=rv32im -mabi=ilp32 -O2
  -ffreestanding -fno-builtin -fno-pic -fno-pie -nostdlib
  -Wl,-e,min_branch -Wl,-Ttext=0x10000 -Wl,--no-relax
  -o <RUN>/min_rv32im.elf
  <MIN>/c_baseline/min.c <MIN>/rv32im/min_branch.S <MIN>/rv32im/min_branchless.S
```

Clang driver另加 `--target=riscv32-unknown-elf -fuse-ld=lld`。`rv32_build.log`保存實際命令與輸出。ELF沒有作業系統啟動程式；`-e,min_branch`只是連結入口，不能直接在Mac或Windows CPU原生執行。Python直譯器會各別設定參數與返回位址後執行三個函式。

## 4. 反組譯驗證與三版本比較

只反組譯本次RUN的ELF，不用歷史文字代替。確認三函式符號及各自範圍，逐條核對：

- C baseline：由指定編譯器實際產生，不假設所有工具鏈都相同。
- Branch：有號blt、選值addi及返回；mv與ret等偽指令以實際展開後計數。
- Branchless：有號slt、sub、xor、and、xor及返回。
- 每個機器碼及分支目的位址都應和來源語意相符；只有函式名稱存在不足以證明全部正確。

工具使用ELF的函式符號大小逐條讀32-bit機器碼作靜態統計；動態計數從函式進入至返回測試呼叫端，包含返回、不含呼叫端及框架。現有函式沒有helper；若未來改成helper，動態範圍可能包含helper，靜態函式本體與動態全路徑必須分開說明。

條件分支是opcode 0x63；jal/jalr另列控制轉移，不能把返回算成條件分支。v1.2.1驗證實際返回目標與保存暫存器，不要求固定ret機器碼。保存暫存器檢查是本測試介面的有限驗證，並非所有RISC-V函式的完整ABI認證；未支援的指令不能直接判為函式功能錯誤。

## 5. 測資、預期結果及歷史對照

原14筆完整輸入及預期答案見 [原始測試](../src/references/validation/2026-10-23-gcc15/source_snapshot/tests/test_min.c)，包括老師範例 `(3,-2)→-2`、`(5,5)→5`，及INT32_MIN／MAX。新增生成部分仍是33×33網格與固定種子20261018的4,096筆，合計5,199筆列表項目；每函式與Python signed MIN比對。不是5,199筆互不重複輸入，更非2^64全域窮舉。

以下只是2026-10-18附件對照，不是新執行必然答案：

| 函式 | 靜態指令（含返回） | 14筆動態 | 14筆條件分支 | taken／not-taken |
|---|---:|---:|---:|---:|
| GCC C min_s32 | 4 | 46 | 14 | 10／4 |
| min_branch | 3 | 38 | 14 | 4／10 |
| min_branchless | 6 | 84 | 0 | 0／0 |

14筆有4筆a<b：C為4×4+10×3=46，Branch為4×2+10×3=38，Branchless為14×6=84。`(46-38)/46×100%=17.39%`僅是動態指令減少率，不是實測加速比（Speedup）、週期或功耗改善。新編譯器若產生不同C機器碼，應記錄新數字與原因，不改舊附件。

## 6. 紀錄、保存與再次重現

完整run應保留：run_status、來源SHA-256、版本標籤、Python與OS、主機及RISC-V編譯器版本、實際argv、完整stdout/stderr、原始ELF、ELF雜湊、measurements JSON/Markdown；本指南再加objdump版本、反組譯、補充環境、產物雜湊及包含全部內容的ZIP。只有新run實際產生的資料才可當本次證據。

再次重現應使用同一版本來源及工具，在另一個全新run重做上面流程；比較來源雜湊、編譯器／flags、測試筆數與函式統計。不要求ELF一定逐位相同（可能含路徑等差異），若機器碼不同須說明。不要從另一個run複製ELF補入缺件。

`passed`表示腳本主機C與RISC-V測試完成；`completed_with_native_skip`表示明確略過主機，不能算完整通過；`failed`表示本流程未完成。遇不支援指令，記錄工具限制而非宣稱MIN錯誤。缺工具、只靜態閱讀、保存機器碼重播與重新編譯執行須各別報告。

## 7. 歷史缺件與證據說明

2026-10-18的ELF、完整log及當次雜湊未提交，沒有補造。2026-10-21檢查文件也未提交。保存機器碼重播只能支持該機器碼及直譯器結果，不等於來源重新編譯。詳見 [證據索引](../src/references/README.md) 與 [維護紀錄](CP2_MAINTENANCE.md)。

本指南命令的ZIP只封存該次run；重現仍需同SHA來源。專案內精選證據包以目錄及package_sha256.json保存，來源快照另列；未納入重複ZIP或主機EXE。原始artifacts_sha256.json屬原run清單，含未選入檔案，不是精選包清單。直譯器100條上限屬工具預算，超限不是功能錯誤的證明。命令log旁的stdout/stderr.bin保存原始輸出位元組。

保存紀錄包含先前Bash語法與失敗停止檢查；以下專案路徑版的完整Bash成功流程未端到端執行。新來源重建的成功證據來自Windows的Python入口及後續GNU objdump操作，不將不同驗證範圍混用。


## 8. 已保存49組邊界與22項回歸

額外49組的全部輸入、答案及指令數見[邊界JSON](../src/references/validation/2026-10-23-gcc15/gcc_run_fixed/additional_signed_boundaries.json)，每函式49/49、共147次，0失敗；原5,199筆與生成規則未改。這是當時新ELF直譯結果，不是本指南的CLI會自動另跑49組。

如需重現有限邊界驗證，可使用相同快照驗證器的ELF32及run_function介面，遍歷JSON所列7×7輸入，將結果寫到全新run；不改寫舊JSON。這個額外操作不是check_cp2.py預設的5,199筆入口，必須另存並標日期及ELF SHA。

流程回歸入口為source_snapshot/tests/test_cp2_flow.py，需以CP2_VALIDATION_ROOT指定證據目錄以外的全新輸出目錄，再用python -B執行；非零退出即停止。保存的原22/22結果見[回歸log](../src/references/validation/2026-10-23-gcc15/flow_regressions.log)。後續重跑需另存結果，不改原log或當成原測試。


### 額外49組的新run核對範例

以下只讀指定的新ELF並新建結果JSON；環境變數必須先設定為本次新產物與不存在的結果檔。它不覆寫保存結果，也不包含在預設5,199筆入口內：

```python
import datetime, hashlib, importlib.util, itertools, json, os
from pathlib import Path
script = Path("src/references/validation/2026-10-23-gcc15/source_snapshot/tests/check_cp2.py")
spec = importlib.util.spec_from_file_location("cp2_boundary", script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
elf_path = Path(os.environ["NEW_ELF"]).resolve()
out = Path(os.environ["NEW_BOUNDARY_JSON"]).resolve()
evidence = script.resolve().parents[2]
if out == evidence or evidence in out.parents:
    raise SystemExit("拒絕寫入保存證據包")
elf = module.ELF32(elf_path)
values = [-2147483648, -2147483647, -1, 0, 1, 2147483646, 2147483647]
rows = []
for fn in module.FUNCTIONS:
    for a, b in itertools.product(values, repeat=2):
        result = module.run_function(elf, fn, a, b)
        if result["result"] != min(a, b):
            raise SystemExit(f"FAIL: {fn} {a} {b}")
        rows.append({"function": fn, "a": a, "b": b,
                     "expected": min(a, b), "actual": result["result"]})
record = {"kind": "new_ELF_interpreter_execution", "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "ELF_sha256": hashlib.sha256(elf_path.read_bytes()).hexdigest(),
          "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
          "vectors_per_function": 49, "passed": len(rows), "failed": 0, "results": rows}
with out.open("x", encoding="utf-8") as handle:
    json.dump(record, handle, ensure_ascii=False, indent=2)
```

此程式片段提供可核對的操作方法；該片段為重現方法，不是另一份已執行的49筆紀錄。


## 9. 保存結果摘要與來源

| 項目 | 保存結果 | 直接證據 |
|---|---|---|
| main來源三函式新ELF | 各5,199/5,199 PASS | [measurements.json](../src/references/validation/2026-10-23-gcc15/gcc_run_fixed/measurements.json) |
| 額外signed邊界 | 各49/49 PASS | [邊界JSON](../src/references/validation/2026-10-23-gcc15/gcc_run_fixed/additional_signed_boundaries.json) |
| 原流程回歸 | 22/22 PASS | [原回歸log](../src/references/validation/2026-10-23-gcc15/flow_regressions.log) |
| 搬遷後流程回歸 | 22/22 PASS，退出碼0 | [新回歸狀態](../src/references/validation/2026-10-23-gcc15/integration_check/relocated_flow_status.json) |
| RISC-V來源重建 | GCC15.2.0、RV32IM／ILP32、-O2，成功 | [編譯log](../src/references/validation/2026-10-23-gcc15/gcc_run_fixed/rv32_build.log) |
| 13條函式機器碼比對 | 新／歷史位址與機器碼一致 | [比較JSON](../src/references/validation/2026-10-23-gcc15/gcc_run_fixed/comparison_to_historical.json) |

上述main來源驗證與dev min_s32.S分列。原始來源重建紀錄使用Windows的Python入口及GNU工具，完整Bash操作範例不冒充已完成的流程。沒有Ripes、Spike、QEMU、真實硬體或CPU cycles量測，也沒有實測Speedup。


## 10. dev來源的獨立組譯與反組譯

dev的min_s32.S與main快照分開組譯。以下Bash範例只建立全新目錄，不執行原Makefile的clean，也不覆寫rv32im下的既有物件。PROJECT_ROOT為專案根目錄，DEV_RUN為不存在的輸出目錄，RV_CC／RV_OBJDUMP為支援RISC-V的實際工具路徑：

```bash
bash -euo pipefail <<'DEV_BUILD'
set -C
: "${PROJECT_ROOT:?未設定專案根目錄}"
: "${DEV_RUN:?未設定全新輸出目錄}"
: "${RV_CC:?未設定RISC-V編譯器}"
: "${RV_OBJDUMP:?未設定RISC-V objdump}"
if [ -e "$DEV_RUN" ]; then
  printf '拒絕覆寫既有目錄：%s\n' "$DEV_RUN" >&2
  exit 1
fi
mkdir "$DEV_RUN"
"$RV_CC" -march=rv32im -mabi=ilp32 -c "$PROJECT_ROOT/src/rv32im/min_s32.S" -o "$DEV_RUN/min_s32.o"
"$RV_OBJDUMP" -d -M no-aliases "$DEV_RUN/min_s32.o" > "$DEV_RUN/min_s32.disasm.txt"
DEV_BUILD
```

這是獨立重建操作方法，不宣稱在文件定稿階段重新執行。dev物件檔僅含該Assembly，沒有直接執行測試框架；靜態3條與原14筆38條路徑推算，不等於main來源5,199／49筆驗證。
