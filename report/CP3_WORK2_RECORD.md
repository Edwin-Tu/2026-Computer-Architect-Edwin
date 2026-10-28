# CP3 工作二：修改與驗證紀錄

## 範圍與負責人

- 工作二分配：林佳宏，MIN 語意規格、虛擬碼、範例及 baseline 語意核對。
- 日期：2026-10-28。
- 本次執行：ChatGPT／Codex 依林佳宏要求協助整理與驗證；這不是本人已獨立撰寫、理解或完成全組 CP3 的聲明。
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
| [CP3 工作二報告稿](CP3.md) | 本組根目錄 report 的工作二整合稿，六段結構及 AI 使用說明；尚缺工作三／四的完整內容 |
| [語意檢查程式](../instructions/02_MIN/tests/check_cp3_semantics.py) | 讀取原 C 測資，對照保存 Branch ELF、語意模型及暫存器寫回 |
| [報告索引](README.md) | 新增工作二報告與本紀錄的入口 |

原有 C、Assembly、CP1／CP2 報告、測資、保存 ELF 及其證據包均不修改。本次不處理既有證據包 README 的雜湊不一致，也不把它算入工作二成果。不加入先前聊天的額外加速探索、替代 baseline 最佳化或週期數。

## 驗證方式與結果

執行環境：Python 3.11.4。從本機倉庫根目錄執行：

```bash
python -B instructions/02_MIN/tests/check_cp3_semantics.py
```

本次實際輸出：

```text
Original C table + preserved branch ELF + custom semantic model: 14/14 PASS
Baseline: static core/function = 2/3; dynamic core/function = 24/38; taken = 4/14
Preserved branch ELF boundary grid: 49/49 PASS
Custom semantic model boundary/writeback checks: 343/343 PASS
Python: 3.11.4; semantic checker v1.0; CP2 subset interpreter v1.0
No native compilation, custom-opcode execution, cycles or speedup measured.
```

- 49 筆為七個邊界值的兩兩組合；343 次為同一 49 筆分別套用七種暫存器配置，不是 343 組互不重複的輸入。
- ELF 的 SHA-256 先與保存的 measurements.json 比對後才執行。
- 此次實際執行 `min_branch` 的保存機器碼，沒有重新編譯目前來源，沒有執行自訂 opcode。
- 語意模型的暫存器重疊及 `x0` 測試是模型檢查，不代表已完成處理器實作。
- 不將這次結果說成重跑原有 5,199 筆、原生 C 測試或 22 項流程回歸。

## 個人確認與後續整合

目前文件及可重現檢查已由 AI 協助準備完成，尚待林佳宏本人閱讀、理解與實際修改確認。最終 AI 使用說明需列出本人真正核對與修改的項目，不能預填已完成的個人行為。工作三編碼與工作四完整比較、索引及全組貢獻聲明由對應組員整合；本機 commit 不是繳交完成證明。
