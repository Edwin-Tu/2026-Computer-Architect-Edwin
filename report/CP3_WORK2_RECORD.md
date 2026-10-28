# CP3 工作二：修改與驗證紀錄

## 範圍與負責人

- 工作二分配：林佳宏，MIN 語意規格、虛擬碼、範例及 baseline 語意核對。
- 日期：2026-10-28。
- 實際分工：林佳宏提出工作二範圍，要求對照教師規定、實際跑測試、區分舊證據、排除額外加速探索、保留本機 commit 並準備組員接手；ChatGPT／Codex 執行文件／程式編輯、測試及本機 Git 操作。
- 不填寫其他組員貢獻或本次比例；正式比例仍須全組依實際工作確認。

## 基底與本機 Git

本機倉庫從使用者提供的 `2026-Computer-Architect-Edwin-main (1).zip` 建立，沒有從其他 dev ZIP 搬入草稿。ZIP 本身沒有原倉庫 `.git` 歷史，因此本機第一個 commit 僅代表 ZIP 匯入，不代表原 GitHub 提交或由本人撰寫所有既有檔案。

- 本機匯入 commit：`08ef11f`（`chore: import provided main ZIP as local baseline`）。
- 本機分支：`dev/lin-jiahong-cp3-semantics`。
- Git author 沿用本機既有設定 `Kuro-Lin`；新增內容的 AI 協助範圍如實揭露，不以 author 名稱證明獨立撰寫。
- 未設定遠端；未 push、建立 PR、合併或建立繳交 tag。
- 後續若要套回正式倉庫，應只審查並搬移工作二的變更，不推送 ZIP 匯入歷史；是否同步須另獲使用者指示。

## 本次新增與整理

| 檔案 | 內容 |
|---|---|
| [正式語意規格](../instructions/02_MIN/spec/README.md) | 公式、定義域、結果範圍、相等及極值、溢位、虛擬碼、七筆範例、baseline 與指令數、5 Whys |
| [CP3 工作二報告](CP3.md) | 本組根目錄 report 的工作二內容，六段結構及 AI 使用說明；工作三／四的完整內容另行整合 |
| [語意檢查程式](../instructions/02_MIN/tests/check_cp3_semantics.py) | 讀取原 C 測資，對照保存 Branch ELF、語意模型及暫存器寫回 |
| [報告索引](README.md) | 新增工作二報告與本紀錄的入口 |

原有 C、Assembly、CP1／CP2 報告、測資、保存 ELF 及其證據包均不修改。本次不處理既有證據包 README 的雜湊不一致，也不把它算入工作二成果。不加入先前聊天的額外加速探索、替代 baseline 最佳化或週期數。

## 驗證方式與結果（目前 v1.1）

執行環境：Python 3.11.4。從本機倉庫根目錄執行：

```bash
python -B instructions/02_MIN/tests/check_cp3_semantics.py
```

本次實際輸出：

```text
Document example tables: 11/11 PASS
Source snapshots + preserved ELF hash/instruction shape: PASS
Original C table + preserved branch ELF + custom semantic model: 14/14 PASS
Baseline: static core/function = 2/3; dynamic core/function = 24/38; taken = 4/14
Preserved branch ELF boundary grid: 49/49 PASS
Custom semantic model boundary/writeback checks: 343/343 PASS
Python: 3.11.4; semantic checker v1.1; CP2 subset interpreter v1.0
No native compilation, custom-opcode execution, cycles or speedup measured.
```

- 49 筆為七個邊界值的兩兩組合；343 次為同一 49 筆分別套用七種暫存器配置，不是 343 組互不重複的輸入。
- ELF 的 SHA-256 先與保存的 measurements.json 比對後才執行。
- 目前 C、Branch、原 14 筆 C 測資與快照內容一致（僅將換行格式正規化）；此檢查不是重新編譯或 C 原生執行。
- 逐筆檢查規格七筆、報告四筆範例及規格的十六進位答案，避免只測模型而漏掉文件抄寫錯誤。
- 此次實際執行 `min_branch` 的保存機器碼，沒有重新編譯目前來源，沒有執行自訂 opcode。
- 語意模型的暫存器重疊及 `x0` 測試是模型檢查，不代表已完成處理器實作。
- 不將這次結果說成重跑原有 5,199 筆、原生 C 測試或 22 項流程回歸。

## 此輪修訂紀錄

依使用者要求，Codex 實際執行以下修改：

1. 補明零、兩負數與 INT32_MIN／MAX 的行為，以及虛擬碼中暫存器編號與數值的區別。
2. 將 AI 提醒式文字改為本次實際操作與責任說明，保留 AI 揭露，沒有虛構本人獨立改寫或手算。
3. 將檢查程式升為 v1.1，新增文件表格、目前來源對照與保存 ELF 指令形狀檢查；寫回測試使用獨立的有號解讀方法核對模型。
4. 更新 MIN 首頁、報告及測試入口，讓組員能直接找到工作二內容與重現命令。

本輪另檢查六份修改文件中的 43 個本機檔案／章節連結，均通過；白話說明為 92 字元，未超過 200 字。逐位元組比對提供的 main ZIP，確認舊核心、14 組測資、CP1／CP2 報告及歷史證據未修改。

上述記錄代表使用者提出要求、AI 實際編輯與驗證的協作過程；不將其替換成未發生的「本人已獨立完成」聲明。課程要求個人理解，文件及測試不能單獨證明這件事。

## 工作二審核與全組整合界線

- 工作二文件：公式、定義域、結果範圍、邊界與溢位、虛擬碼、至少三筆含邊界範例、baseline 片段與靜態／動態指令數皆已提供。
- 驗證：以本節列出的可重現檢查為準；原始證據與新增模型結果分列。
- 格式：根目錄 `report/CP3.md` 作為整合入口，`spec/README.md` 保留工作二完整內容。老師 §5.2 的全倉庫扁平目錄規定與現有多層結構仍有差異，需由全組統一整理或取得教師同意；本次未搬動其他組員的既有程式／證據。
- 工作三編碼、工作四完整比較、全組貢獻比例、組長核准與正式 tag／PR 尚不在本次交付範圍。
- 本機 commit 已保存；交接套件僅供離線接手，不能代表 GitHub 已收件、帳號已關聯或老師已收到提交。
