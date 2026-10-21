# MIN — CP2 實驗執行指令與紀錄

> 適用環境：macOS Terminal（zsh）、`2026-Computer-Architect-Edwin/instructions/02_MIN` 專案。  
> **原則：只讀取原始專案；在桌面新建實驗資料夾執行編譯與測試。原始檔案、Git 與 GitHub 均不修改。**  
> 測量範圍：RV32IM 函式本體的靜態／動態指令數、條件分支數；**不是** CPU 週期或實際執行時間。

## 0. 確認專案路徑與工具

在 Terminal 輸入以下指令（**後續步驟請使用同一個 Terminal 視窗**，以保留 `$EXP` 變數）：

```bash
PROJECT="$HOME/Project/2026-Computer-Architect-Edwin"
SRC="$PROJECT/instructions/02_MIN"

cd "$PROJECT"
pwd

# 檢查來源檔案是否存在；缺少任何檔案請先停止
for file in \
  "$SRC/c_baseline/min.c" \
  "$SRC/c_baseline/min.h" \
  "$SRC/tests/test_min.c" \
  "$SRC/rv32im/min_branch.S" \
  "$SRC/rv32im/min_branchless.S" \
  "$SRC/tests/check_cp2.py"; do
  if [ ! -f "$file" ]; then
    echo "缺少檔案：$file"
  fi
done

riscv64-elf-gcc --version
riscv64-elf-objdump --version
python3 --version
cc --version
```

編譯器若無法執行，應先安裝／修復工具鏈；不要假設實驗結果已經產生。

## 1. 建立獨立實驗目錄，複製來源（不動原檔）

```bash
EXP="$HOME/Desktop/CP2_RECORD_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$EXP/src/c_baseline" "$EXP/src/rv32im" "$EXP/tools" "$EXP/records"

cp "$SRC/c_baseline/min.c" \
   "$SRC/c_baseline/min.h" \
   "$SRC/tests/test_min.c" \
   "$EXP/src/c_baseline/"

cp "$SRC/rv32im/min_branch.S" \
   "$SRC/rv32im/min_branchless.S" \
   "$EXP/src/rv32im/"

cp "$SRC/tests/check_cp2.py" "$EXP/tools/"

# 檢查原始 C 基準與實驗副本完全一致
cmp "$SRC/c_baseline/min.c" "$EXP/src/c_baseline/min.c" \
  && echo "C baseline 內容一致"

find "$EXP/src" "$EXP/tools" -type f | sort
printf '\n實驗資料夾：%s\n' "$EXP"
```

> 如果開了新的 Terminal 視窗，`$EXP` 可能已不存在。請重新指定上次產生的完整路徑，例如：  
> `EXP="$HOME/Desktop/CP2_RECORD_20261018_131340"`（這只是範例，請改成你自己的實際名稱）。

## 2. 執行 C Baseline 測試（14 組）

```bash
set -o pipefail

cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror \
  "$EXP/src/c_baseline/min.c" \
  "$EXP/src/c_baseline/test_min.c" \
  -o "$EXP/records/test_min"

"$EXP/records/test_min" 2>&1 | tee "$EXP/records/01_c_baseline.log"
```

預期最後一行：

```text
Result: 14/14 tests passed.
```

**僅在輸出確實顯示全部通過時，才在報告中記錄 PASS。**

## 3. 執行 RV32IM 測試與指令統計

使用你安裝的 `riscv64-elf-gcc`，編譯以下三種函式：

- `min_s32`：原本 `min.c` 經 GCC `-O2` 編譯的基準。
- `min_branch`：手寫 Branch（分支）版本。
- `min_branchless`：手寫 Branchless（無分支）版本。

```bash
python3 "$EXP/tools/check_cp2.py" \
  --compiler riscv64-elf-gcc \
  2>&1 | tee "$EXP/records/02_rv32im.log"
```

腳本執行流程：產生 RV32IM ELF32 → 用 Python RV32I 子集直譯器執行函式 → 驗證 **14 + 33×33 + 4096 = 5199** 組輸入 → 輸出指令數統計。

**正確性測試用 5,199 組；表格中的「動態指令數（14）」只統計原始 CP1 的 14 組。** 指令計數包含 `ret`；條件分支數不包含 `ret/jalr`。

預期輸出會包含（以實際輸出為準）：

```text
All implementations passed 5199 input pairs.
Evidence saved to .../build/measurements.json and .../build/measurements.md
```

此腳本會在 **`$EXP/build/`** 寫入機器碼及測量結果，不會修改原始 `02_MIN`。

## 4. 取得反組譯（Disassembly）

```bash
riscv64-elf-objdump -d -M no-aliases \
  "$EXP/build/min_rv32im.elf" \
  2>&1 | tee "$EXP/records/03_disassembly.txt"
```

確認輸出含 `min_s32`、`min_branch`、`min_branchless` 三個函式名稱。以 `objdump` 輸出的**實際機器碼**解釋靜態指令數差異。

## 5. 保存編譯器版本、來源驗證資料

```bash
{
  echo "Experiment date: $(date '+%Y-%m-%d %H:%M:%S %z')"
  echo "Project: $PROJECT"
  echo "Experimental copy: $EXP"
  echo
  sw_vers
  echo
  riscv64-elf-gcc --version | head -n 1
  riscv64-elf-objdump --version | head -n 1
  python3 --version
  echo
  echo "Source SHA-256:"
  shasum -a 256 \
    "$SRC/c_baseline/min.c" \
    "$EXP/src/c_baseline/min.c" \
    "$EXP/src/rv32im/min_branch.S" \
    "$EXP/src/rv32im/min_branchless.S" \
    "$EXP/tools/check_cp2.py"
} 2>&1 | tee "$EXP/records/04_environment.txt"

# 供報告使用的指令數彙總表
cat "$EXP/build/measurements.md"

# 確認紀錄檔實際存在
find "$EXP/records" "$EXP/build" -maxdepth 1 -type f | sort
```

## 6. （選用）打包本次實驗證據

只打包桌面**實驗副本**中的紀錄與統計，不修改原始專案：

```bash
cd "$EXP"
zip -r "${EXP}_evidence.zip" records build/measurements.md build/measurements.json
printf 'ZIP: %s\n' "${EXP}_evidence.zip"
```

## 7. 實驗數據怎麼寫進 CP2

請抄錄自己 `measurements.md` 的實際數據。以下僅為 **2026-10-18 當次 GCC 16.2.0、`-O2` 實驗的對照值**，**不是**每台電腦必然相同的結果：

| 函式 | 靜態指令數（含 ret） | 動態指令數（14 組，含 ret） | 動態條件分支（14 組） |
|---|---:|---:|---:|
| `min_s32` | 4 | 46 | 14 |
| `min_branch` | 3 | 38 | 14 |
| `min_branchless` | 6 | 84 | 0 |

當次 Branch 相對於 C 基準的動態指令減少率：`(46 - 38) / 46 × 100% ≈ 17.39%`。這個百分比**不是** CPU 執行時間加速率，也**不能**直接代表所有編譯器的結果。

### CP2 報告方法說明（可作為檢查清單）

- 編譯器版本、`-march=rv32im -mabi=ilp32 -O2` 與使用的測資須註明。
- 靜態指令數由 ELF 函式本體 32-bit 指令統計；動態指令數由 Python RV32I 子集直譯器追蹤真實 ELF 機器碼取得。
- 分支統計只算**條件分支**（`beq/bne/blt/bge/...`），不把 `ret` 當條件分支。
- 應區分正確性測試的 5,199 組與效能統計的 14 組。
- 目前未測量 CPU cycles（週期）、CPI 或真實硬體執行時間。
- 報告內容與 AI 使用揭露仍須由組員自行理解、確認與撰寫。
