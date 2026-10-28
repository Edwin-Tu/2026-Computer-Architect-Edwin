# CP2參考與驗證證據索引

## 既有分支成果

本分支[min_s32.S](../rv32im/min_s32.S)、[原反組譯](../rv32im/min_s32.disasm.txt)與[CP2報告](../../report/CP2.md)維持來源歸屬。報告前段14筆38條動態數為路徑推算，不改寫為已完成5,199筆。

## 2026-10-23來源重建與測試

[證據包說明](validation/2026-10-23-gcc15/README.md)保存main@e084ba0的C／Branch／Branchless快照、新ELF、工具版本、實際命令、原始log及SHA-256。所有導覽均為專案內相對路徑；原log內的絕對路徑僅為當時來源資訊。

| 證據 | 用途 |
|---|---|
| [成功狀態與來源SHA](validation/2026-10-23-gcc15/gcc_run_fixed/run_status.json) | 新來源建置及有限直譯器驗證 |
| [5,199筆與統計](validation/2026-10-23-gcc15/gcc_run_fixed/measurements.json) | 三函式各5,199/5,199 |
| [signed邊界](validation/2026-10-23-gcc15/gcc_run_fixed/additional_signed_boundaries.json) | 各49/49，共147次 |
| [新ELF](validation/2026-10-23-gcc15/gcc_run_fixed/min_rv32im.elf) | 5,080 bytes，與來源SHA相符 |
| [新反組譯](validation/2026-10-23-gcc15/gcc_run_fixed/disassembly_new_gcc15.txt) | 13條函式機器指令 |
| [新舊比較](validation/2026-10-23-gcc15/gcc_run_fixed/comparison_to_historical.json) | 與歷史文字機器碼／位址一致，非整檔ELF |
| [主機C log](validation/2026-10-23-gcc15/gcc_run_fixed/native_test.log) | 真正重新編譯執行14/14 |
| [實際入口log](validation/2026-10-23-gcc15/build_and_test_fixed_entry.log) | 實際argv與輸出 |
| [原22項回歸](validation/2026-10-23-gcc15/flow_regressions.log) | mock、fixture與歷史重播分開解讀 |
| [工具版本與SHA](validation/2026-10-23-gcc15/tools.json) | GCC／GNU工具與LLVM限制 |
| [首次失敗](validation/2026-10-23-gcc15/first_attempt/run_status.json) | CRLF假失敗不改成成功 |
| [來源及檔案清單](validation/2026-10-23-gcc15/provenance_manifest.json) | 保存來源、位元組雜湊與排除清單 |
| [完整包SHA清單](validation/2026-10-23-gcc15/package_sha256.json) | 目前精選證據包的完整性 |

歷史GCC16.2附件保持原位元組於source_snapshot/references，見[證據包](validation/2026-10-23-gcc15/README.md)。歷史ELF與完整當次log未提交，不能以新ELF代替。沒有實測cycles或Speedup。

## 技術參考

- [RISC-V RV32I規格](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html)：有號比較與控制轉移；沿用2026-10-23既有存取紀錄。
- [RISC-V psABI](https://riscv-non-isa.github.io/riscv-elf-psabi-doc/)：參數、返回與暫存器；沿用既有存取紀錄。
- [本分支HOMEWORK.md](../../HOMEWORK.md)：專案保存的課程規範。

## 基底保留的歷史附件

- [歷史GCC16反組譯](disassembly_gcc16.txt)
- [歷史測量JSON](measurements.json)
- [歷史測量摘要](measurements.md)

上述檔案隨3e169d5保留原位元組；來源快照中的對應附件支持既有驗證工具重現，沒有覆寫歷史數據。
