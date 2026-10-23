# CP2 — MIN RV32IM 實作與指令統計

## 1. 本次目標

以 RV32IM 基本整數指令實作 32-bit 有號 MIN，並列出函式本體的靜態與動態指令數、分支數。

## 2. 設計內容

### 2.1 呼叫介面與演算法

實作位於 [`rv32im/min_s32.S`](../rv32im/min_s32.S)，使用標準 ILP32 呼叫慣例：`a0` 傳入 `rs1`，`a1` 傳入 `rs2`，結果由 `a0` 回傳。`blt` 是**有號**小於比較；當 `rs1 < rs2` 時直接回傳 `rs1`，否則把 `rs2` 移至 `a0`。兩數相等時回傳 `rs2`，其值與 `rs1` 相同。

```asm
min_s32:
    blt     a0, a1, .Lreturn_rs1
    mv      a0, a1
.Lreturn_rs1:
    ret
```

`mv` 與 `ret` 是組合器偽指令；展開後分別是 `addi a0, a1, 0` 和 `jalr x0, 0(ra)`。因此實際機器指令只使用 RV32I，符合 RV32IM 限制，也未使用任何自訂 MIN opcode。

### 2.2 可重現建置

由專案根目錄執行：

```sh
make -C instructions/02_MIN/rv32im clean all
```

Makefile 使用 `riscv64-elf-gcc -march=rv32im -mabi=ilp32` 組譯，並以 `riscv64-elf-objdump -d -M no-aliases` 產生反組譯檔。輸出 `min_s32.o` 與 `min_s32.disasm.txt` 位於 `instructions/02_MIN/rv32im/`；反組譯可核對偽指令展開與靜態指令數。

### 2.3 靜態與動態指令數

計數範圍限定為 `min_s32` 函式本體，不含呼叫端、測試框架與回傳後的指令。靜態數以偽指令展開後的機器指令計；動態數以 CP1 的 14 筆案例各呼叫一次函式計，`blt` 每次都會執行一次。

| 執行路徑 | 條件 | 執行指令 | 動態指令數 | 分支指令數 | 分支結果 |
|---|---|---|---:|---:|---|
| 回傳 `rs1` | `rs1 < rs2` | `blt`, `jalr` | 2 | 1 | taken |
| 回傳 `rs2` | `rs1 >= rs2` | `blt`, `addi`, `jalr` | 3 | 1 | not taken |

| 統計範圍 | 靜態指令數 | 動態指令數 | 動態分支數 | taken / not taken |
|---|---:|---:|---:|---:|
| 單次函式呼叫（rs1 < rs2） | 3 | 2 | 1 | 1 / 0 |
| 單次函式呼叫（rs1 >= rs2） | 3 | 3 | 1 | 0 / 1 |
| CP1 14 筆測資，各呼叫一次 | 3 | 38 | 14 | 4 / 10 |

靜態三條機器指令為 `blt`、`addi`、`jalr`。動態總數由 4 次 taken 路徑的 2 條，加上 10 次 not-taken 路徑的 3 條計得，即 `4 × 2 + 10 × 3 = 38`；這裡是依測資與指令路徑計算，並非模擬器輸出的全程 retired-instruction 數。

| CP1 案例 | rs1 | rs2 | 結果 | 分支 | 函式動態指令數 |
|---:|---:|---:|---:|---|---:|
| 1 | 3 | -2 | -2 | not taken | 3 |
| 2 | 5 | 5 | 5 | not taken | 3 |
| 3 | 10 | 20 | 10 | taken | 2 |
| 4 | 20 | 10 | 10 | not taken | 3 |
| 5 | -10 | -20 | -20 | not taken | 3 |
| 6 | 0 | 0 | 0 | not taken | 3 |
| 7 | 0 | -1 | -1 | not taken | 3 |
| 8 | 0 | 100 | 0 | taken | 2 |
| 9 | -100 | 100 | -100 | taken | 2 |
| 10 | `INT32_MAX` | `INT32_MIN` | `INT32_MIN` | not taken | 3 |
| 11 | `INT32_MIN` | 0 | `INT32_MIN` | taken | 2 |
| 12 | `INT32_MAX` | 0 | 0 | not taken | 3 |
| 13 | `INT32_MIN` | `INT32_MIN` | `INT32_MIN` | not taken | 3 |
| 14 | `INT32_MAX` | `INT32_MAX` | `INT32_MAX` | not taken | 3 |

上述動態數只計算 MIN 函式；若要計算整個測試程式，還須納入呼叫端、迴圈、資料載入與比較等指令，並註明模擬器及計數範圍。

## 3. 結果與分析

本函式僅需一次有號比較，再視結果選擇回傳值。兩種路徑都執行一條分支指令；taken 路徑為 2 條機器指令，not-taken 路徑為 3 條。相等時使用 `rs2`，不影響 MIN 語意。特別是 `INT32_MAX` 與 `INT32_MIN` 的案例可區分有號 `blt` 和無號比較。

### 路徑與證據

課程規範 [HOMEWORK.md §5.4](../../../HOMEWORK.md) 提到 `src/rv32im/`，但目前倉庫把各題內容依題目放在 `instructions/<題目>/`，因此本題程式與建置輸出位於 `instructions/02_MIN/rv32im/`。本報告和 Makefile 均使用此實際路徑；若全組決定切換到課程規範路徑，須同步移動目錄並更新索引與建置命令。

重建指令 `make -C instructions/02_MIN/rv32im clean all` 已成功執行。環境版本為 `riscv64-elf-gcc (GCC) 16.2.0`、`GNU objdump (GNU Binutils) 2.47.20260726`。產生的 `min_s32.o` 為 `elf32-littleriscv` 物件檔；`min_s32.disasm.txt` 顯示機器指令依序為 `blt`、`addi`、`jalr`，與靜態指令數 3 相符。動態指令數 38 仍是依 CP1 測資及控制流程推算，沒有使用模擬器量測整個測試程式的 retired-instruction 數。

## 4. 遭遇的問題與解法

本題的比較必須是有號比較；若誤用 `bltu`，負數會被當成很大的無號值，結果可能錯誤。實作使用 `blt`，並以 `INT32_MIN`、`INT32_MAX` 與跨正負號案例檢查分支方向。另一個容易誤算的地方是 `mv`、`ret` 為偽指令，報告的靜態指令數依展開後的 `addi`、`jalr` 計算。

## 5. 白話說明

MIN 先看第一個數是不是比第二個數小。如果是，就保留第一個；否則改用第二個。即使兩個數一樣，選哪一個都會得到相同結果。電腦只需要做一次有號比較和一次條件分支，接著回傳較小的值；分支走哪一邊會讓執行指令數差一條。

## 6. AI 使用說明

本 CP2 初稿使用 Codex 協助整理規格、撰寫組合語言初版及推導分支路徑計數；本次由 Codex 在本機執行 GNU RISC-V 工具鏈重建，並核對反組譯中的三條機器指令。動態數為依 CP1 14 筆案例推算，尚未以模擬器量測；組員提交前應自行理解並核對程式、測資和計數範圍。
