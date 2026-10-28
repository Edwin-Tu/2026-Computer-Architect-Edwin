# mac_demo:MAC 自訂指令示範

本資料夾是教師示範題 `MAC`(乘加)的完整材料:指令編碼、C 參考實作、5 級 pipeline 時序模型、時鐘與 CPU Time 的 benchmark。學生不得選此題,由教師或助教於課堂示範。

## 一、指令定義

### 1.1 rd 累加器形式(預設)

```
mac rd, rs1, rs2        rd = rd + rs1 × rs2     (32-bit 有號整數,取低 32 位元,溢位回繞)
```

- R-type,操作碼 custom-0(`0001011`,0x0B),`funct3 = 0`,`funct7 = 0`
- 範例:`mac a0, a1, a2` 的機器碼為 `0x00C5850B`
- `rd` 同時是累加來源與結果目的,因此需要 3 個讀埠(rd、rs1、rs2)與 1 個寫埠

### 1.2 R4 形式(替代方案)

```
mac4 rd, rs1, rs2, rs3  rd = rs3 + rs1 × rs2
```

- R4 型式:`rs3` 位於 [31:27],`funct2 = 0`,`funct3 = 1`,操作碼仍為 custom-0
- 不依賴 rd 的舊值,因此連續的 MAC 之間沒有累加鏈相依
- 與 `funct3 = 0` 的 rd 形式不會互相誤判(測試已涵蓋)
- 同樣需要 3 個讀埠

### 1.3 `rd = x0` 語意

- 讀取 x0 時值為 0,寫入 x0 時結果被丟棄
- 由 `apply_mac(regs, rd, rs1, rs2)` 模擬,測試位於 `test_r4_and_x0.py`

### 1.4 溢位政策

結果為乘積加累加值的**低 32 位元**(回繞)。

- `(2^31 − 1)^2 = 0x3FFFFFFF00000001`,低 32 位元為 `0x00000001`
- 低 32 位元與 `mul` 一致,與標準版比較時公平

## 二、檔案一覽

| 檔案 | 說明 |
|---|---|
| `mac.h` | `mac_insn` 內嵌組語(RISC-V)與 host 端等價的 C 分支、函式宣告 |
| `mac.c` | `dot_ref`(標準乘加)與 `dot_mac`(使用 `mac_insn`) |
| `test_mac.c` | C 測試:基本運算、負數、溢位、空陣列、已知值、200 組隨機比對 |
| `riscv_probe.c` | 以 `mac_insn` 包裝成函式,供 RISC-V 交叉編譯與反組譯檢查 |
| `mac_encoding.py` | rd 形式與 R4 形式的編碼與解碼、`apply_mac`、黃金模型、點積參考 |
| `test_mac_encoding.py` | rd 形式編碼與黃金模型的測試 |
| `test_r4_and_x0.py` | R4 形式的編碼、往返、互斥,以及 x0 語意 |
| `test_overflow.py` | 溢位政策(低 32 位元與 `mul` 一致) |
| `test_riscv_encoding.py` | 以 RISC-V 交叉編譯器檢查 `mac_insn` 的機器碼(無工具鏈時跳過) |
| `pipeline_model.py` | 5 級 pipeline 週期模型,含 forwarding、load-use 停頓、分支 flush、`mac_lat` 參數 |
| `test_pipeline_model.py` | 週期模型的測試 |
| `test_mac_latency.py` | MAC 延遲參數對週期數的影響 |
| `render_pipeline.py` | 由排程產生 `pipeline_mac.md`、`.svg`、`.gif` |
| `test_render_pipeline.py` | 圖表產生的測試 |
| `pipeline_mac.md` / `.svg` / `.gif` | MAC 迴圈前兩次迭代的時序圖 |
| `benchmark/dotbench.py` | 點積 benchmark:指令數、CPU Time、加速比,支援展開參數 `unroll` |
| `benchmark/clock_model.py` | 依指令類別 CPI 的時鐘模型與損益平衡計算 |
| `benchmark/clock_model_report.py` | 時鐘模型參數表 |
| `benchmark/host_timing.c` | 主機實測計時(參考點積,非 RISC-V 量測) |
| `benchmark/test_*.py` | benchmark 與時鐘模型的測試 |
| `Makefile` | 測試與實驗的入口 |

> 注意:`pipeline_model.py` 與時序圖屬於**期中後**的內容。在教師尚未講授 pipeline 前,學生不應依此計算 cycle 數或 clock 減少數。

## 三、環境需求

- Python 3.10 以上,並安裝 `Pillow`(產生 GIF 用)
- C 編譯器(`cc` 或 `gcc`),支援 C11
- RISC-V 交叉編譯器 `riscv64-elf-gcc`(僅 `make check-riscv` 需要,沒有時會跳過)

```bash
python3 -m pip install Pillow
```

## 四、執行方式

| 指令 | 內容 |
|---|---|
| `make test` | C 測試 + 全部 Python 測試 |
| `make test-c` | 只跑 C 測試 |
| `make test-py` | 只跑 Python 測試 |
| `make check-riscv` | RISC-V 交叉編譯並反組譯,檢查 MAC 機器碼 |
| `make bench-model` | 時鐘模型參數表 |
| `make bench-host` | 主機計時實驗 |
| `make bench-unroll` | 展開 4 倍的點積 benchmark |
| `make bench-latency` | MAC 延遲 1、2、3 拍的比較 |
| `python3 render_pipeline.py` | 重新產生時序圖 |
| `make clean` | 清除編譯產物 |

目前結果:Python 測試 61 項與 C 測試全部通過,RISC-V 檢查通過。

## 五、Benchmark 設計

### 5.1 工作負載

| ID | 類型 | N | 說明 |
|---|---|---|---|
| B1 | 全範圍隨機 | 64、256、1024 | 32-bit 有號整數,含溢位回繞 |
| B2 | INT8 範圍 | 64、256、1024 | 值域 [−128, 127] |
| B3 | 邊界值 | 64 | 交替 `0x7FFFFFFF` 與 `0x80000000` |

輸入由固定 seed `2026` 產生。每個工作負載都會先比對 MAC 迴圈與參考結果,不一致則標示 FAIL。

### 5.2 指令數與 CPU Time

- 迴圈本體:標準版 4 條(`lw`、`lw`、`mul`、`add`),MAC 版 3 條(`lw`、`lw`、`mac`)
- 迴圈開銷:4 條(兩個指標遞增、計數遞減、`bnez`)
- 每元素指令數 = 本體 + 4 / unroll
- CPU Time = 指令數 × CPI × 週期時間

### 5.3 結果一:展開 1 倍(unroll 1,CPI = 1)

| 工作負載 | N | 標準 IC | MAC IC | 正確性 | T 比 1.0 | T 比 1.1 | T 比 1.2 |
|---|---:|---:|---:|:---:|---:|---:|---:|
| B1 | 64 | 512 | 448 | OK | 1.14x | 1.04x | 0.95x |
| B1 | 256 | 2048 | 1792 | OK | 1.14x | 1.04x | 0.95x |
| B1 | 1024 | 8192 | 7168 | OK | 1.14x | 1.04x | 0.95x |
| B2 | 64 / 256 / 1024 | 同 B1 | 同 B1 | OK | 1.14x | 1.04x | 0.95x |
| B3 | 64 | 512 | 448 | OK | 1.14x | 1.04x | 0.95x |

### 5.4 結果二:展開 4 倍(unroll 4,CPI = 1)

| 工作負載 | N | 標準 IC | MAC IC | 正確性 | T 比 1.0 | T 比 1.1 | T 比 1.2 |
|---|---:|---:|---:|:---:|---:|---:|---:|
| B1 | 64 | 320 | 256 | OK | 1.25x | 1.14x | 1.04x |
| B1 | 1024 | 5120 | 4096 | OK | 1.25x | 1.14x | 1.04x |
| B2 | 64 / 256 / 1024 | 同 B1 | 同 B1 | OK | 1.25x | 1.14x | 1.04x |
| B3 | 64 | 320 | 256 | OK | 1.25x | 1.14x | 1.04x |

**解讀**:展開 4 倍後,迴圈開銷被攤提,加速比從 8/7 ≈ 1.14 提高到 5/4 = 1.25。

## 六、時鐘模型實驗(依指令類別的 CPI)

假設:`lw` CPI = 2,`add`、`addi`、`bnez` CPI = 1,`mul` 與 `mac` 的 CPI 為變數。

| mul CPI | MAC CPI | 標準 cycles/元素 | MAC cycles/元素 | 損益平衡 T 比 | T 比 1.0 時 CPU Time 比 |
|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 10 | 9 | 1.111 | 0.900 |
| 1 | 3 | 10 | 11 | 0.909 | 1.100 |
| 3 | 1 | 12 | 9 | 1.333 | 0.750 |
| 3 | 3 | 12 | 11 | 1.091 | 0.917 |
| 5 | 1 | 14 | 9 | 1.556 | 0.643 |
| 5 | 3 | 14 | 11 | 1.273 | 0.786 |

**解讀**:損益平衡 T 比是 MAC 的週期時間能容忍的上限。

## 七、MAC 延遲對 pipeline 週期的影響(N = 1024,標準版 mul = 1 拍)

| MAC 延遲(拍) | 標準週期 | MAC 週期 | 加速比 |
|---:|---:|---:|---:|
| 1 | 11266 | 10242 | 1.10x |
| 2 | 11266 | 11266 | 1.00x |
| 3 | 11266 | 12290 | 0.92x |

**解讀**:MAC 多一拍,在標準乘法也是一拍的假設下,優勢就消失。延遲 2 拍的情況與公開 MAC 實作資料中的兩級管線設計相符(見第九節)。

## 八、主機計時實驗(非 RISC-V 量測)

`benchmark/host_timing.c` 量測主機上 `dot_ref` 的執行時間,先驗證結果一致,再重複量測並輸出中位數與範圍。

| 執行 | N | 中位數 ns/呼叫 | 最小 | 最大 | 變異範圍 |
|---|---:|---:|---:|---:|---:|
| 第 1 次 | 1024 | 396.0 | 366.5 | 405.0 | 9.7% |
| 第 2 次 | 1024 | 661.0 | 544.0 | 1093.5 | 83.1% |

**重要提醒**:兩次中位數相差約 67%,變異範圍差異很大。這表示背景負載與電源狀態會明顯影響結果。報告時必須同時給出執行次數與變異範圍。這個實驗只說明量測方法,**不能**用來推論自訂指令的加速效果。

## 九、文獻對照與設計建議

以下建議依據網路文獻與教科書整理,並標示與本資料夾的對應關係。

| 文獻或資料 | 發現 | 對本示範的意義 |
|---|---|---|
| RISC-V 非特權 ISA 手冊 | custom-0/1 保留給自訂擴充,自訂編碼不得用於標準擴充 | 目前 custom-0 的使用符合規範,應在作業中引用 |
| RISC-V P 擴充相關研究(2025) | 封包化乘加(MACC)是獨立的指令形式,佔用大量操作碼空間;SIMD 乘加在矩陣乘法上有明顯加速 | 可作為 v3 的延伸題,說明 packed MAC 的取捨 |
| ARM SMLAD(Cortex-M DSP 擴充) | 雙 16-bit 乘加,使用獨立的累加暫存器 `Ra`,與 R4 形式相近 | 支持保留 R4 形式作為替代方案;雙 16-bit 版本可作為延伸 |
| 公開的 RISC-V MAC 實作資料(GitHub 專案) | MAC 單元可採用兩級管線(Booth 乘法 + 累加),延遲為 2 拍 | 報告時應同時列出 mac_lat = 1 與 mac_lat = 2 的情境 |
| Tensilica TIE 相關文獻 | 客製化指令以描述語言定義,並自動產生編譯器與硬體 | 可作為學生說明「規格到實作」流程的參考 |

### 9.1 建議的後續改進

1. **報告兩種延遲情境**:mac_lat = 1 為理想情境,mac_lat = 2 對應文獻中常見的兩級管線實作。若 mac_lat = 2,在本模型中沒有加速,需要在結論中說明。
2. **加入封包化的 MAC 變體**:參考 ARM SMLAD 的雙 16-bit 形式,在 INT16 資料上每條指令做兩次乘加,可以量化 SIMD 的效益與硬體成本。
3. **命名與文件對齊 RISC-V P 擴充**:若未來要與標準擴充比較,應使用相同的術語,避免學生混淆。
4. **在作業中引用規範原文**:custom-0 的規範應直接引用手冊,而不是口頭說明。

## 十、限制與誠實揭露

1. **指令數**依手寫的迴圈結構推算,不是模擬器實測。
2. **CPI 與週期時間**都是假設值。`T_mac / T_std` 不是硬體合成結果。
3. **pipeline 模型**是抽象模型,未與 RTL 或 FPGA 對照。
4. **正確性**以 Python 的 MAC 迴圈模型與參考結果比對。C 端在 host 上以等價的純 C 分支驗證;RISC-V 端只檢查編譯器輸出的機器碼,未在模擬器上執行。
5. **R4 形式**只做編碼與語意的比較,未實作硬體。
6. 所有數字在報告中都應標示為「模型估計」或「主機量測」,不得混用。

## 十一、可重現性

- 亂數 seed 固定為 `2026`
- 主機計時結果會因機器狀態而異,重現時請記錄機器型號、作業系統版本與執行時的負載

## 十二、相關文件

- 作業說明與學生規範:倉庫根目錄的 `HOMEWORK.md`
- 課程計畫與行事曆:倉庫根目錄的 `README.md`

## 參考來源

- [RISC-V Instruction Set Manual, Volume I: Unprivileged Architecture](https://docs.riscv.org/reference/isa/_attachments/riscv-unprivileged.pdf)
- [Unprivileged RISC-V ISA — CVA6 documentation](https://docs.openhwgroup.org/projects/cva6-user-manual/04_cv32a65x/riscv/unpriv.html)
- [RV-VP²: Unlocking the Potential of RISC-V Packed-SIMD for Embedded Processing](https://link.springer.com/chapter/10.1007/978-3-031-78380-7_5)
- [A SIMD MAC RISC-V Extension with Approximate Multipliers for Accelerating CNN Inference in Tiny Embedded Devices](https://cris.fau.de/publications/338504527/)
- [ARMv7-M Architecture Reference Manual — Multiply instructions](https://developer.arm.com/documentation/ddi0403/d/Application-Level-Architecture/The-ARMv7-M-Instruction-Set/Data-processing-instructions/Multiply-instructions)
- [CMSIS-Core (Cortex-M): Intrinsic Functions for SIMD Instructions](https://arm-software.github.io/CMSIS_6/latest/Core/group__intrinsic__SIMD__gr.html)
- [Computer Organization and Design RISC-V Edition — Elsevier Educate (Edition 2)](https://www.educate.elsevier.com/book/details/9780128203316)
- [RISC-V-CUSTOM-INSTRUCTION-MULTIPLY-ACCUMULATE-HARDWARE(GitHub,兩級 MAC 實作資料)](https://github.com/VinayGorige/RISC-V-CUSTOM-INSTRUCTION-MULTIPLY-ACCUMULATE-HARDWARE)
- [Hardware/Software Instruction Set Configurability (Tensilica, DAC 2001)](https://www.princeton.edu/~rblee/ELE572Papers/Fall04Readings/ComputerArchitecture/wang_Tensilica.pdf)
