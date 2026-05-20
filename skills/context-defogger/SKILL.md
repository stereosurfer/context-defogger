---
name: context-defogger
description: Use when turning provided AI-user conversation logs into public-facing thinking-context article embryos. The skill extracts thinking milestones, user intent, AI proposals, user corrections or rejections, turning points, lessons, and article groupings. It treats GitHub issues and PRs only as background anchors unless the user explicitly asks for handoff or operational status.
metadata:
  short-description: Defog messy AI chats into thinking context
---

# Context Defogger

## Purpose

Turn provided conversation content into public-facing thinking-log material.

This skill is not a project handoff writer, PR summarizer, release note writer, or publishing pipeline. Its job is to find the thinking: what the user was trying to do, how the AI interpreted it, where that interpretation failed or was modified, which intentions survived, and what principle or lesson emerged.

## Output Target

Produce editorial article embryos that can later be rendered into fixed HTML.

The primary output should read like a shaped idea, not a section-by-section summary. Use structure to support judgment, not to replace it.

Do not generate website code, Cloudflare deployment steps, or interactive UI unless the user explicitly switches to the publishing phase.

## Output Persistence

By default, return the article embryo in chat unless the user asks to save it.

When saving output, use this default root:

```text
~/Documents/Context Defogger/
```

Before creating this folder, ask the user to confirm the location. If the user
chooses another folder, use that folder for the current run and mention it in
the output metadata.

Use this naming convention for a single article:

```text
YYYY-MM-DD_HHMMSS__source-title__context-defogger.md
```

Use this naming convention when a source conversation becomes an article series:

```text
YYYY-MM-DD_HHMMSS__source-title__context-defogger/
  index.md
  01__short-article-slug.md
  02__short-article-slug.md
```

Keep filenames filesystem-safe: lowercase slugs, ASCII punctuation, no private
thread ids unless the user explicitly wants them as anchors. Do not save private
conversation exports, raw JSONL, screenshots, or local artifacts unless the user
separately asks for an export/archive workflow.

## Core Rule

Group by thinking tension, not by GitHub object.

Issues, PRs, branches, commits, and file paths are background anchors. Mention them only when they help locate the story or explain why a turn happened. Do not repeat GitHub details that already exist in GitHub unless those details caused a decision, correction, or lesson.

## Workflow

1. Read the provided conversation as the source of truth for the thinking process.
2. Extract event cards for moments where something changed:
   - user stated, clarified, or corrected intent
   - AI proposed a framing, plan, or solution
   - user accepted, modified, rejected, or narrowed the AI proposal
   - a false assumption was exposed
   - a decision or reusable principle emerged
   - multiple issues/PRs were revealed to share one deeper problem
3. Cluster event cards into article candidates by shared thinking tension.
4. For each article candidate, decide whether it is publishable:
   - it has a real question, not just a task
   - it has a before/after shift
   - it contains a user-intent analysis
   - it contains an AI-proposal calibration analysis
   - it leaves behind a lesson, principle, or reusable distinction
5. Draft the article embryo around three currents:
   - problem current: what core contradiction this milestone was really handling
   - user-intent current: what the user was trying to achieve, what held, and what had to be revised
   - AI-calibration current: what the AI proposed, what assumptions it carried, and why the user accepted, modified, or rejected it
6. Use the schema in `references/extraction_schema.md` as a support layer, not a writing template.
7. If the result feels like a segmented summary, rewrite it as a short argument about how the thinking was calibrated.

## User Intent Analysis

Do not treat the first user request as the final intent. Infer intent from the whole conversation, especially corrections.

For each major intent, classify it as:

- `成立`: the intent remained valid and shaped the final direction
- `修正後成立`: the intent survived, but its framing or implementation changed
- `不成立`: the intent was rejected, contradicted, or replaced
- `未定`: the conversation did not settle it

Always include the reason. Prefer evidence from the user's own corrections.

## AI Proposal Calibration

For each important AI proposal, identify:

- what the AI proposed
- what assumption the proposal carried
- whether the user accepted, modified, or rejected it
- why the user responded that way
- what the proposal became after calibration

This section is central. The public value is often in showing how the human corrected the machine's framing.

The strongest article often says something like:

> The point was not simply that the AI helped with X. The interesting part was how the user's intent, the AI's proposal, and the limits of the situation corrected one another until the real shape of the work appeared.

Prefer this kind of connective thesis over a list of accepted / modified / rejected items.

## Narrative Shape

Start from a claim, not from a log.

Good article embryos usually follow this motion:

1. Name why the added element matters.
2. Reframe the work from a shallow description into the deeper calibration problem.
3. Show the three currents in one coherent paragraph or short passage.
4. State the public takeaway in language a reader can reuse.

Example shape:

```markdown
這兩個元素很關鍵，因為它們會讓文章從「我學到了什麼」變成「這段思考是怎麼被校準的」。

這段里程其實有三條主線一起推進：問題主線、用戶意圖主線、AI 方案校準主線。問題主線在問，表面任務背後到底是哪個核心矛盾；用戶意圖主線在問，使用者真正想達成什麼，哪些成立，哪些被證偽或修正；AI 校準主線則在問，AI 提了什麼方案，哪些被接受、修改或拒絕，原因是什麼。

所以文章最後不該只是「AI 幫我做了什麼」，而是人的意圖、AI 的提案、現實的限制，三者怎麼互相修正。
```

Use headings sparingly in the public-facing draft. If headings make the output feel like a checklist, collapse the material into prose.

## Automatic Article Splitting

Use these rules to merge events into one article:

- Merge when several issues/PRs share the same thinking tension.
- Merge when one correction explains multiple later decisions.
- Merge when the same user intent is tested across several AI proposals.
- Merge when the final lesson only makes sense after seeing the whole chain.

Use these rules to split articles:

- Split when events are only time-adjacent but not conceptually linked.
- Split when two lessons would compete for the headline.
- Split when one article would need more than one "real problem" section.
- Split when a GitHub object is merely background evidence for another article.

When unsure, create a short "split decision" note explaining both options and choose the article grouping that best preserves the thinking arc.

If several articles share one milestone but have distinct lessons, treat them as an article series:

- Keep one shared `overall_theme`.
- Give each article one central tension and one public takeaway.
- Preserve the sequence when later articles depend on earlier corrections.
- Do not force the series into one long article if the headlines would compete.
- Do not split into separate unrelated outputs if the reader needs the shared milestone to understand why the ideas unfolded together.

## Tone

Write for public readers who care about product thinking, workflow design, and human-AI collaboration.

Avoid private operational detail, exhaustive GitHub recap, and insider shorthand. Keep the article brief concrete enough to be credible, but focused on the thought process.

Prefer concrete phrasing over vague analytical filler.

Weak:

- "使用者一路追問，把 AI 的方案逼得更精準。"
- "AI 的方案因此被校準成比較保守的設計。"
- "這段對話真正的核心是..."

Better:

- "使用者接著問了三件事：圖片能不能匯出，`.md/.py/.json/.yaml` 這類檔案怎麼辦，AI 產生的計畫或 artifact 算不算附件。"
- "校準後的設計是：真實檔案用 hash 去重，Markdown 保留穩定附件 id，找不到的檔案寫進 manifest，`--include-assets` 必須明確開啟。"
- "這個問題從『有沒有外掛』變成『能不能把找到的方法做成下次可重用的流程』。"

When a sentence says "became clearer", "was calibrated", "was pushed further", or "the real issue was", check whether it names the actual question, decision, or rejected option. If not, rewrite it.

Use this concrete chain when possible:

```text
User asked / corrected X.
That exposed or rejected AI assumption Y.
The retained design became Z.
```

Support notes should preserve three editorial anchors when available:

- Trigger line: the user sentence or question that changed the direction.
- AI assumption: the proposal or hidden assumption that was accepted, modified, or rejected.
- Retained design: the concrete decision that survived into the output.

## Quality Checks

Before finalizing:

- Can the title be understood without knowing the repo?
- Does each article have one central tension?
- Are user intentions separated from AI proposals?
- Are rejected or modified AI proposals explained fairly?
- Are "facts from conversation" separated from interpretation?
- Are GitHub details only used as anchors?
- Would this still be worth reading after the issue/PR is old?
- Does the public draft have a thesis, or is it just a segmented recap?
- Can the three currents be felt in the prose without forcing the reader through a form?
- If there are several article candidates, are they a real series or just over-splitting?
- Do abstract phrases point to concrete user questions, AI proposals, or final design choices?

## Test And Revision Loop

When the user provides sample conversations for testing:

1. Run the extraction once.
2. Compare the output against `references/test_cases.md` if the scenario resembles one of the cases.
3. Ask which article grouping, intent classification, or AI-calibration reading feels wrong.
4. Revise the extraction rules before expanding into publishing or HTML output.
