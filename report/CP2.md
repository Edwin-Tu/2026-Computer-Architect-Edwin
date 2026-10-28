# CP2 — MIN RV32IM 實作與指令統計

## 1. 目標

以 RV32IM 基本整數指令實作 32-bit 有號 MIN，並列出函式本體的靜態與動態指令數、分支數。

## 2. 設計內容

### 2.1 呼叫介面與演算法

實作位於 [`rv32im/min_s32.S`](../src/rv32im/min_s32.S)，使用標準 ILP32 呼叫慣例：`a0` 傳入 `rs1`，`a1` 傳入 `rs2`，結果由 `a0` 回傳。`blt` 是**有號**小於比較；當 `rs1 < rs2` 時直接回傳 `rs1`，否則把 `rs2` 移至 `a0`。兩數相等時回傳 `rs2`，其值與 `rs1` 相同。

```asm
min_s32:
    blt     a0, a1, .Lreturn_rs1
    mv      a0, a1
.Lreturn_rs1:
    ret
```

`mv` 與 `ret` 是組合器偽指令；展開後分別是 `addi a0, a1, 0` 和 `jalr x0, 0(ra)`。因此實際機器指令只使用 RV32I，符合 RV32IM 限制，也未使用任何自訂 MIN opcode。

### 2.2 可重現建置

既有Makefile將物件與反組譯輸出至rv32im目錄。為保留歷史產物，重新核對dev來源時使用[實驗指南的全新輸出目錄流程](CP2_MIN_執行指令與實驗紀錄.md#10-dev來源的獨立組譯與反組譯)，不改寫原物件或反組譯。

Makefile 使用 `riscv64-elf-gcc -march=rv32im -mabi=ilp32` 組譯，並以 `riscv64-elf-objdump -d -M no-aliases` 產生反組譯檔。輸出 `min_s32.o` 與 `min_s32.disasm.txt` 位於 `src/rv32im/`；反組譯可核對偽指令展開與靜態指令數。

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

### 2.4 main來源的C、Branch與Branchless設計

以下整理e084ba0及3e169d5保存的既有設計。這組來源與dev原min_s32.S分列，指令數依歷史反組譯及保存的新ELF證據核對。

原有 C 函式：

```c
int32_t min_s32(int32_t rs1, int32_t rs2)
{
    return (rs1 < rs2) ? rs1 : rs2;
}
```

#### 2.4.1 Branch：條件分支實作

以下為歷史附件保存的關鍵機器指令（`addi rd, rs, 0` 相當於暫存器複製）：

```asm
min_branch:
    blt  a0, a1, done  # 若 a0 < a1，a0 已是答案
    addi a0, a1, 0     # 否則回傳 a1
done:
    jalr zero, 0(ra)   # 返回（ret）
```

當 `a0 < a1` 時只執行 `blt`、`jalr` 共 **2 條**；當 `a0 >= a1` 時還要執行 `addi`，共 **3 條**。條件比較使用有號 `blt`，不是無號比較。

#### 2.4.2 Branchless：遮罩選擇實作

```asm
min_branchless:
    slt  t0, a0, a1
    sub  t0, zero, t0
    xor  t1, a0, a1
    and  t1, t1, t0
    xor  a0, a1, t1
    jalr zero, 0(ra)
```

`slt` 產生 0/1；`sub t0, zero, t0` 將它轉為 `0x00000000` 或 `0xFFFFFFFF` 的 **Mask（遮罩）**；隨後以 `xor`、`and` 依遮罩選擇較小值。此版本不含條件分支，但每次固定執行 **6 條**，而且會使用 `t0`、`t1` 兩個 caller-saved（呼叫端保存）暫存器。

#### 2.4.3 編譯器產生的 C Baseline

歷史附件使用 GCC 16.2.0、`-O2` 編譯原有 C 程式，實際反組譯為：

```asm
min_s32:
    bge  a0, a1, 10008
    addi a1, a0, 0
    addi a0, a1, 0
    jalr zero, 0(ra)
```

此版本在 `a0 < a1` 時依序執行 `bge`、兩個 `addi`、`jalr`，共 **4 條**；否則跳過第一個 `addi`，共 **3 條**。這是**歷史GCC16.2.0的特定輸出**，不能當作所有編譯器都會產生的固定結果。

#### 2.4.4 5 Whys：為什麼選擇 Branch 作為本次指令數較少的方案？

1. **為什麼 Branch 的 14 組動態指令較少？**保存的直譯器計數為38條，C Baseline 為 46 條，差 8 條。
2. **為什麼差 8 條？**在 14 組測資中有 4 組符合 `a0 < a1`；這類輸入每次 Branch 執行 2 條，GCC C Baseline 執行 4 條，合計少 `4 × 2 = 8` 條。
3. **為什麼 Branch 在這些輸入只要 2 條？**`a0` 已經是答案，`blt` 可以直接跳到 `jalr`，不用搬移資料。
4. **為什麼 GCC C Baseline 在相同輸入執行 4 條？**歷史反組譯顯示先用 `addi` 把 `a0` 複製到 `a1`，再複製回 `a0`，形成兩次可避免的暫存器搬移。
5. **為什麼不能據此宣稱 Branch 普遍更快？**比較結果依賴 GCC 16.2.0 的實際編譯產物與測資分布；先前 Clang 17 的參考實驗曾產生 3 條的 C Baseline，且本次未量測 Pipeline（管線）週期或實際執行時間。


## 3. 結果與分析

本函式僅需一次有號比較，再視結果選擇回傳值。兩種路徑都執行一條分支指令；taken 路徑為 2 條機器指令，not-taken 路徑為 3 條。相等時使用 `rs2`，不影響 MIN 語意。特別是 `INT32_MAX` 與 `INT32_MIN` 的案例可區分有號 `blt` 和無號比較。

### 路徑與證據

課程規範 [HOMEWORK.md §5.4](../HOMEWORK.md) 指定 `src/rv32im/`。本分支已將 MIN 程式從舊 `instructions/02_MIN/rv32im/` 搬至此位置，正式報告位於根目錄 `report/`。本報告的現行路徑與 Makefile 以目前目錄為準；下段舊命令只保留作歷史執行紀錄，不能作為目前重現命令。

07736e2既有報告記錄重建指令 `make -C instructions/02_MIN/rv32im clean all` 執行成功。其記載的環境版本為 `riscv64-elf-gcc (GCC) 16.2.0`、`GNU objdump (GNU Binutils) 2.47.20260726`。產生的 `min_s32.o` 為 `elf32-littleriscv` 物件檔；`min_s32.disasm.txt` 顯示機器指令依序為 `blt`、`addi`、`jalr`，與靜態指令數 3 相符。動態指令數 38 仍是依 CP1 測資及控制流程推算，沒有使用模擬器量測整個測試程式的 retired-instruction 數。

## 4. 遭遇的問題與解法

本題的比較必須是有號比較；若誤用 `bltu`，負數會被當成很大的無號值，結果可能錯誤。實作使用 `blt`，並以 `INT32_MIN`、`INT32_MAX` 與跨正負號案例檢查分支方向。另一個容易誤算的地方是 `mv`、`ret` 為偽指令，報告的靜態指令數依展開後的 `addi`、`jalr` 計算。

## 5. 白話說明

MIN 先看第一個數是不是比第二個數小。如果是，就保留第一個；否則改用第二個。即使兩個數一樣，選哪一個都會得到相同結果。電腦只需要做一次有號比較和一次條件分支，接著回傳較小的值；分支走哪一邊會讓執行指令數差一條。

## 6. 來源重建與驗證結果（2026-10-23）


### 6.1 來源與符號界線

第1–5節說明dev@07736e2的`rv32im/min_s32.S`實作及14筆路徑推算。2026-10-23來源重建驗證的對象為：main@e084ba0的C baseline、Branch及Branchless，核心未改，驗證器為v1.2.1。它們保存於[來源快照](../src/references/validation/2026-10-23-gcc15/README.md)，不是取代本分支核心。尤其本分支Assembly `min_s32`與證據ELF中由C編譯的`min_s32`是不同來源，不能混為同一驗證對象。

沒有以同名符號或相似指令，推論本分支的min_s32.S也完成以下5,199／49筆測試。本分支原38條動態指令仍是依14筆推算；新證據的38條是另一個min_branch函式的直譯執行計數。

### 6.2 已保存的實際結果

| 驗證對象 | 既有輸入 | 另行signed邊界 | 靜態指令（含返回） | 原14筆動態指令 | 全5,199筆動態指令 |
|---|---:|---:|---:|---:|---:|
| C baseline編成的min_s32 | 5,199/5,199 PASS | 49/49 PASS | 4 | 46 | 18,184 |
| Branch min_branch | 5,199/5,199 PASS | 49/49 PASS | 3 | 38 | 13,010 |
| Branchless min_branchless | 5,199/5,199 PASS | 49/49 PASS | 6 | 84 | 31,194 |

5,199＝原14筆＋33×33網格1,089筆＋固定種子20261018隨機4,096筆，是列表項目而非互不重複輸入。另49組為INT32_MIN、INT32_MIN+1、-1、0、1、INT32_MAX-1、INT32_MAX的7×7組合，每函式另存，共147次，0失敗；也可能與既有輸入重複。

保存的主機C原生重編譯執行14/14，主機GCC14.2.0；RISC-V使用xPack GCC15.2.0、GNU Binutils2.45、RV32IM／ILP32及-O2，從原C與Assembly重新組譯連結後，以Python RV32I子集合直譯器v1.2.1執行新ELF。不是保存機器碼重播，也不是在Windows原生執行RISC-V。

保存的流程回歸22/22 PASS，含mock、合成fixture及一項歷史機器碼重播；不能當作22次真正編譯。新GNU反組譯的4+3+6＝13條函式機器碼及位址與歷史GCC16.2文字一致；歷史ELF未提交，不能比較新舊ELF整檔。詳細來源SHA、實際argv、工具版本、成功／失敗紀錄見[證據索引](../src/references/README.md)。

### 6.3 功能與效能的限制

直譯器只支援本次所需RV32I子集合，保存暫存器及返回檢查屬有限ABI驗證，並非完整ISA／ABI認證。原14筆動態統計包含函式返回、不含呼叫端及框架。C與Branch條件分支各14次，taken／not-taken分別10／4與4／10；Branchless沒有條件分支，返回jalr另計。

(46−38)/46×100%＝17.39%只是指令減少率。沒有Ripes、Spike、QEMU、真實硬體、CPU cycles、CPI或實際時間量測，沒有實測Speedup結論，也不是全部2^64輸入對窮舉。原始log中的歷史絕對路徑僅保留來源資訊；目前入口均採專案內相對路徑。


## 7. 結論

dev來源的min_s32.S以有號blt選取較小值，靜態3條，依原14筆輸入推算動態38條。main來源的C baseline、Branch及Branchless已由未修改的來源重新建置，三函式各通過5,199筆及額外49筆邊界檢查；流程回歸22/22。main新ELF的13條函式機器碼與歷史文字一致，但這些結果不直接驗證dev的同名Assembly。

在保存測資及編譯器輸出下，main Branch的動態指令數少於C baseline與Branchless；這只能支持指令數比較，不能證明CPU執行時間或週期加速。Ripes、Spike、QEMU、真實硬體及CPU cycles量測尚未進行。

四位組員的分工與比例見[貢獻聲明](CP2_CONTRIBUTIONS.md)。
