# MIN — CP3 工作二交付與組內整合

本專案題目為 **MIN：兩個 32-bit 有號整數取小**，不是其他題目的作業。現在交付工作二的語意規格、虛擬碼、測試範例及 baseline 對照；工作三的編碼與工作四的完整比較、全組貢獻聲明仍由負責組員整合。

## 接手閱讀順序

1. [報告索引](report/README.md)：唯一 CP3 報告入口及前後一致性規則。
2. [CP3 報告](report/CP3.md)：目前工作二內容；全組只整合這一份 CP3.md。
3. [MIN 正式語意](instructions/MIN/README.md)：工作二完整技術定義，報告摘要須保持一致。
4. [修改與驗證紀錄](report/CP3_WORK2_RECORD.md)：實際操作與證據界線，不另定義指令。

## 目錄

```text
instructions/
  README.md
  MIN/
    README.md
report/
  README.md
  CP1.md
  CP2.md
  CP3.md
  CP3_WORK2_RECORD.md
  figures/
    README.md
src/
  README.md
  c_baseline/
  rv32im/
  tests/
  references/
```

指令目錄只保留 README；實作與測試放在 src，報告集中於 report。老師規定見 [HOMEWORK.md](HOMEWORK.md)。原始來源、測資、機器碼與原始 log 保留；說明文件的相對連結依新位置更新。完整搬動前版本另有本機封存及 Git 歷史，不將老師的其他題目模板列為本組成果。

## 重現工作二驗證

從專案根目錄執行：

```bash
python -B src/tests/check_cp3_semantics.py
python -B src/tests/check_cp3_delivery.py
```

此檢查核對文件範例、原 14 筆測資、保存 Branch ELF 及語意模型，不重新編譯、不執行自訂 opcode，也不量測週期或加速。

## 協作與繳交狀態

目前本機分支為 `dev/1114405029`，所有修改先在組內核對，不直接推送 main。未設定遠端、未 push、未開 PR、未建立繳交 tag。全組貢獻比例及正式繳交流程由全組確認，不以本文件代替。

AI 工具與實際編輯範圍如實列於 [CP3 AI 使用說明](report/CP3.md#6-ai-使用說明)。測試通過不代表工具能代替本人理解。
