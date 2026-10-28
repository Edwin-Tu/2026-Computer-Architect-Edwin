| 指令 | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | C11 | C12 | C13 | C14 | C15 | C16 | C17 | C18 | C19 | C20 | C21 | C22 |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `lw t0, 0(a0)` | IF | ID | EX | MEM | WB |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `lw t1, 0(a1)` |  | IF | ID | EX | MEM | WB |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `mac t3, t0, t1` |  |  | IF | ID | stall | EX | MEM | WB |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `addi a0, a0, 4` |  |  |  |  | IF | ID | EX | MEM | WB |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `addi a1, a1, 4` |  |  |  |  |  | IF | ID | EX | MEM | WB |  |  |  |  |  |  |  |  |  |  |  |  |
| `addi a2, a2, -1` |  |  |  |  |  |  | IF | ID | EX | MEM | WB |  |  |  |  |  |  |  |  |  |  |  |
| `bnez a2, loop` |  |  |  |  |  |  |  | IF | ID | EX | MEM | WB |  |  |  |  |  |  |  |  |  |  |
| `lw t0, 0(a0)` |  |  |  |  |  |  |  |  |  |  | IF | ID | EX | MEM | WB |  |  |  |  |  |  |  |
| `lw t1, 0(a1)` |  |  |  |  |  |  |  |  |  |  |  | IF | ID | EX | MEM | WB |  |  |  |  |  |  |
| `mac t3, t0, t1` |  |  |  |  |  |  |  |  |  |  |  |  | IF | ID | stall | EX | MEM | WB |  |  |  |  |
| `addi a0, a0, 4` |  |  |  |  |  |  |  |  |  |  |  |  |  |  | IF | ID | EX | MEM | WB |  |  |  |
| `addi a1, a1, 4` |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | IF | ID | EX | MEM | WB |  |  |
| `addi a2, a2, -1` |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | IF | ID | EX | MEM | WB |  |
| `bnez a2, loop` |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | IF | ID | EX | MEM | WB |

模型總週期(含 2 次迭代):**22**,最後一拍為 WB = C22。
stall:load-use 停頓(`lw t1` 之後的 `mac` 等待 1 拍)。
累加鏈 `mac t3` → 下一個 `mac t3` 透過 forwarding 不停頓。
`bnez` 跳回後,下一條有效指令的 EX 延後 3 拍(flush 2 拍的錯誤路徑未畫出)。
