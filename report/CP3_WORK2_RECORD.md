# CP3 工作二：修改與驗證紀錄

## 範圍與負責人

- 工作二分配：林佳宏，MIN 語意規格、虛擬碼、範例及 baseline 語意核對。
- 日期：2026-10-28。
- 實際分工：林佳宏提出工作二範圍，要求對照教師規定、實際跑測試、區分舊證據、排除額外加速探索、保留本機 commit 並準備組員接手；ChatGPT／Codex 執行文件／程式編輯、測試及本機 Git 操作。
- 不填寫其他組員貢獻或本次比例；正式比例仍須全組依實際工作確認。

## 基底與本機 Git

本機倉庫從使用者提供的 `2026-Computer-Architect-Edwin-main (1).zip` 建立，沒有從其他 dev ZIP 搬入草稿。ZIP 本身沒有原倉庫 `.git` 歷史，因此本機第一個 commit 僅代表 ZIP 匯入，不代表原 GitHub 提交或由本人撰寫所有既有檔案。

- 本機匯入 commit：`08ef11f`（`chore: import provided main ZIP as local baseline`）。
- 本機分支：`dev/1114405029`，符合 `dev/<學號>`；初版分支名稱已更正。
- Git author 依本人提供的資訊設為 `d14405029-hub <263867770+d14405029-hub@users.noreply.github.com>`，僅設定本倉庫；新增內容的 AI 協助範圍如實揭露，不以 author 名稱證明獨立撰寫。
- 未設定遠端；未 push、建立 PR、合併或建立繳交 tag。
- 後續若要套回正式倉庫，應只審查並搬移工作二的變更，不推送 ZIP 匯入歷史；是否同步須另獲使用者指示。

## 本次新增與整理

| 檔案 | 內容 |
|---|---|
| [正式語意規格](../instructions/MIN/README.md) | 公式、定義域、結果範圍、相等及極值、溢位、虛擬碼、七筆範例、baseline 與指令數、5 Whys |
| [CP3 工作二報告](CP3.md) | 本組根目錄 report 的工作二內容，六段結構及 AI 使用說明；工作三／四的完整內容另行整合 |
| [語意檢查程式](../src/tests/check_cp3_semantics.py) | 讀取原 C 測資，對照保存 Branch ELF、語意模型及暫存器寫回 |
| [報告索引](README.md) | 新增工作二報告與本紀錄的入口 |

本次處理 CP3 工作二及交付目錄的一致性。C、Assembly、測資、保存 ELF、JSON 測量結果與原始 log 保留原位元組；檔案依目前目錄搬動，說明文件的相對連結同步更新。證據包 README 舊雜湊不符另作可追溯的完整性修正，見 `src/references/validation/2026-10-23-gcc15/integrity_update.json`，不偽裝成原紀錄自始一致。不加入額外加速探索、替代 baseline 最佳化或週期數。

## 驗證方式與結果（目前 v1.1）

執行環境：Python 3.11.4。從本機倉庫根目錄執行：

```bash
python -B src/tests/check_cp3_semantics.py
```

本次實際輸出：

```text
Document example tables: 11/11 PASS
Source snapshots + preserved ELF hash/instruction shape: PASS
Original C table + preserved branch ELF + custom semantic model: 14/14 PASS
Baseline: static core/function = 2/3; dynamic core/function = 24/38; taken = 4/14
Preserved branch ELF boundary grid: 49/49 PASS
Custom semantic model boundary/writeback checks: 343/343 PASS
Python: 3.11.4; semantic checker v1.1; baseline RV32I subset interpreter v1.0
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

初次內容審核曾檢查六份修改文件中的 43 個本機檔案／章節連結，均通過；白話說明為 92 字元，未超過 200 字。該次比對確認舊核心、14 組測資、歷史報告及保存產物未修改。後續為符合交付結構而搬動檔案並更新導覽，現在的驗證範圍以最後的目錄審核與交接包紀錄為準。

後續範圍核對：本次修改的對象是 CP3 工作二，不是歷史報告修訂。CP3 文件中的來源說明以具體 baseline、測資與 ELF 表示；工具檔名 `check_cp2.py` 僅為實際載入的既有直譯器檔案名稱，不代表本次交付其他 Checkpoint。

上述記錄代表使用者提出要求、AI 實際編輯與驗證的協作過程；不將其替換成未發生的「本人已獨立完成」聲明。課程要求個人理解，文件及測試不能單獨證明這件事。

## 工作二審核與全組整合界線

- 工作二文件：公式、定義域、結果範圍、邊界與溢位、虛擬碼、至少三筆含邊界範例、baseline 片段與靜態／動態指令數皆已提供。
- 驗證：以本節列出的可重現檢查為準；原始證據與新增模型結果分列。
- 格式：根目錄 `report/CP3.md` 作為唯一整合入口，`instructions/MIN/README.md` 保留工作二完整內容；指令目錄只有 README，實作與證據置於 `src/`，報告及圖表導覽置於根目錄 `report/`。搬動前完整版本已封存，未刪除 Git 歷史或變更核心行為。
- 工作三編碼、工作四完整比較、全組貢獻比例、組長核准與正式 tag／PR 尚不在本次交付範圍。
- 本機 commit 已保存；交接套件僅供離線接手，不能代表 GitHub 已收件、帳號已關聯或老師已收到提交。

## 交接說明一致性修訂

本次統一根目錄 `report/CP3.md` 為唯一報告整合檔，`instructions/MIN/README.md` 為工作二完整技術定義，本紀錄僅記載操作與驗證。搬動前曾將舊目錄索引導回根目錄；目前已集中為根目錄報告索引及 MIN 指令入口，不保留第二份 CP3.md。歷史報告僅同步檔案搬動所需的相對連結，不改寫原測試結論。

接手規則已寫入報告索引：先讀上一位組員的報告、規格、驗證及最近 commit，再編輯自己的段落；語意、範例與計數變更須同時核對所有對應說明。全組編碼與完整比較尚待整合，此狀態在所有 CP3 入口保持一致。離線交接入口只保留一個目前使用的 ZIP；舊套件移入封存區，不作目前成果。

## 目錄與完整性修正

所有目前指令文件集中於 `instructions/MIN/README.md`，原始碼及驗證資料移至 `src/`，歷史報告及目前報告集中於根目錄 `report/`。原有老師的其他題目模板與示範材料另存於工作區外側的本機封存，不列為本組交付。

本次新版本已更正分支名稱、補齊目錄 README 與圖表導覽，修正文件連結及驗證腳本路徑。每筆目前證據清單雜湊與來源 manifest 都須核對通過；原始來源、機器碼、測資及 log 不因修正清單而重寫。

個人理解仍須由本人說明，不能藉由更改文件寫成已理解，也不建立虛構的全組貢獻比例。作者帳號與 noreply 信箱已由本人提供並授權設定；本機 author 可核對，GitHub 實際顯示仍須在組長整合推送後查看。

目前結構的實際重現命令為：

```bash
python -B src/tests/check_cp3_semantics.py
python -B src/tests/check_cp3_delivery.py
```

目錄與完整性檢查實際通過：唯一扁平 MIN 指令目錄、全部目錄 README、唯一根目錄 CP3 報告、145 個本機檔案／章節連結、55/55 目前證據檔案雜湊、44 筆原 provenance 來源雜湊、92 字元白話說明及 `dev/1114405029` 分支名稱。另與輸入 ZIP 比對 42 份來源、機器碼或原始 log，位元組均相同。這些結果不包括 GitHub 帳號綁定、個人理解或全組工作三／四的完成認證。

## 本人授權的 commit 作者更新

本人提供 GitHub 帳號 `d14405029-hub` 與 commit noreply 信箱後，授權更新五筆本機工作二提交的 author／committer。這次僅改提交身分與隨之改變的父提交雜湊，逐筆確認檔案樹、提交訊息、作者日期及提交日期均保留；最初 ZIP 匯入 commit 不改。舊提交仍有本機備份，不會隨交接補丁或專案快照上傳。

| 原提交 | 更新作者後的提交 |
|---|---|
| `bc528d9` | `90fd353` |
| `25736da` | `16a89ff` |
| `fbbd54d` | `fb98a98` |
| `42ec6d2` | `fd0fb9d` |
| `81826bc` | `ccd6948` |

本紀錄的作者資訊修訂另外提交，使用相同的新 author。交接時套用重製後的補丁，組長保留獨立 commit；不要再使用舊作者版本。修改作者身分不等於宣稱本人獨立產出 AI 文字，AI 揭露及既有測試結論不變。未 push、建立 PR 或提交老師端。
