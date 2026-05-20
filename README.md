# Context Defogger

把混亂的 AI 對話，整理成可以公開閱讀的思考脈絡。

Clear messy AI conversations into usable public thinking context.

## 這是什麼 / What It Is

Context Defogger 是一個 Codex Skill。它讀取你提供的 AI 對話內容，提煉出文章胚胎：真正的問題、使用者意圖、AI 的提案與假設、使用者如何修正或拒絕、關鍵轉折，以及最後留下來的設計判斷。

Context Defogger is a Codex skill. It reads AI-user conversation content and extracts article embryos: the real question, user intent, AI proposals and assumptions, user corrections or rejections, turning points, and retained design decisions.

它不是聊天紀錄匯出器，不是專案交接文件產生器，也不是靜態網站產生器。

It is not a chat transcript exporter, a project handoff writer, or a static site generator.

## 它會產出什麼 / What It Produces

- 以自然段落寫成的 article embryos，而不是分段摘要。
- 依照「思考張力」自動分篇。
- 分析哪些使用者意圖成立、哪些被修正、哪些沒有成立。
- 分析 AI 提了什麼方案，哪些被接受、修改或拒絕，以及原因。
- 保留編輯用筆記：觸發句、AI 假設、最後留下來的設計。

- Article embryos written as prose, not checklist summaries.
- Automatic article splitting by thinking tension.
- User-intent analysis: what held, what changed, and what did not survive.
- AI-proposal calibration: what the AI proposed, what the user modified or rejected, and why.
- Support notes with trigger lines, AI assumptions, and retained design choices.

## 為什麼需要它 / Why It Exists

AI 對話裡常常有有價值的推理，但價值通常藏在來回修正裡。Context Defogger 的目標，是把那些霧狀的對話整理成可以重讀、分享、延伸的思考筆記。

AI conversations often contain useful reasoning, but the useful part is usually buried inside back-and-forth correction. Context Defogger turns that fog into notes that can be reread, shared, and built on.

一句話：

Tagline:

> 把混亂 AI 對話除霧成可用的思考脈絡。
>
> Clear messy AI conversations into usable thinking context.

## 如何使用：Codex / How To Use: Codex

Skill 位置：

Skill location:

```text
skills/context-defogger/
```

在 Codex 裡可以這樣說：

In Codex, you can say:

```text
Use $context-defogger to turn this conversation into public thinking-context article embryos.
```

或直接貼一段對話，請它整理：

Or paste a conversation and ask it to process it:

```text
Use $context-defogger on this conversation.
```

## 如何使用：Claude Code / How To Use: Claude Code

這個 repo 也提供 Claude Code 的輕量入口：

This repo also includes lightweight Claude Code entrypoints:

- `CLAUDE.md`：專案記憶入口。
- `.claude/commands/context-defogger.md`：專案 slash command。

- `CLAUDE.md`: project memory entrypoint.
- `.claude/commands/context-defogger.md`: project slash command.

在 Claude Code 裡可以使用：

In Claude Code, use:

```text
/context-defogger
```

Claude Code 入口只指向 canonical skill，不複製另一套規則，避免兩邊漂移。

The Claude Code entrypoints point back to the canonical skill instructions instead of duplicating another rule set.

## 儲存輸出 / Saving Output

預設情況下，Context Defogger 會直接在對話中回覆。

By default, Context Defogger replies in chat.

如果你要求儲存結果，預設位置是：

If you ask it to save the result, the default location is:

```text
~/Documents/Context Defogger/
```

建立這個資料夾前，應該先詢問使用者確認。

It should ask before creating that folder.

單篇文章使用：

Single-article output uses:

```text
YYYY-MM-DD_HHMMSS__source-title__context-defogger.md
```

如果一段對話分成一組系列文，會建立資料夾，裡面包含 `index.md` 和每篇文章。

If one conversation becomes a series, it creates a folder with `index.md` and one Markdown file per article.

## 專案治理 / Repository Governance

這個 repo 使用 ASGK 風格的 source governance：

This repository uses ASGK-style source governance:

- `AGENTS.md`：agent 操作指南。
- `docs/handoff/CURRENT_STATUS.md`：目前狀態與下一步。
- `docs/DOCUMENT_MAP.md` 和 `docs/DOCUMENT_REGISTRY.md`：文件導覽與登錄。
- GitHub issues 和 pull requests 是工作單位的 durable source of truth。

- `AGENTS.md`: agent operating guide.
- `docs/handoff/CURRENT_STATUS.md`: current status and next safe action.
- `docs/DOCUMENT_MAP.md` and `docs/DOCUMENT_REGISTRY.md`: document routing and registry.
- GitHub issues and pull requests are the durable source of truth for work units.

## 非目標 / Non-Goals

- 目前不做 Cloudflare 或靜態 blog 發佈。
- 目前不做 HTML renderer。
- 不是聊天紀錄匯出器。
- 目前不做 package-manager 發佈。

- No Cloudflare or static blog publishing yet.
- No HTML renderer yet.
- Not a transcript exporter.
- No package-manager release yet.

## 授權 / License

本 repo 採用 Apache License 2.0。完整條款請見 `LICENSE`。

This repository is licensed under the Apache License 2.0. See `LICENSE` for the full terms.

本 repo 也包含改寫自 ASGK 的治理 scaffold；相關 Apache-2.0 notice handling 記錄在 `NOTICE`。

This repo also includes adapted ASGK governance scaffold material; Apache-2.0 notice handling is recorded in `NOTICE`.
