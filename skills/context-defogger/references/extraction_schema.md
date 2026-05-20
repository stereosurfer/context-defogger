# Extraction Schema

Use this schema when producing thinking-log article embryos.

The schema is a support layer. The public-facing output should lead with a concise thesis-driven draft, not with a mechanical section outline.

## Batch Summary

```yaml
source_type: conversation
publishing_phase: extraction_only
overall_theme: ""
article_count: 0
series_mode: none | single_milestone_series | separate_articles
github_anchor_policy: "background_only"
open_questions:
  - ""
```

## Article Series

Use this when one conversation milestone produces several article embryos.

```yaml
series_title: ""
series_reason: ""
articles:
  - article_id: ""
    role_in_series: "origin | public_tooling | boundary_design | followup"
    central_tension: ""
    depends_on_previous: true | false
```

## Article Brief

```yaml
article_id: "short-stable-slug"
title: ""
one_sentence_summary: ""
central_tension: ""
publishability: high | medium | low
background_anchors:
  issues: []
  prs: []
  repos: []
  other: []
source_limits:
  - "What is missing, ambiguous, or not live-verified."
```

### Article Embryo

Write this before any detailed evidence table.

```markdown
### Working Title

### Core Passage

2-5 paragraphs that make the article's central argument in natural prose. The passage should connect:

- 問題主線: 這段里程到底在處理什麼核心矛盾
- 用戶意圖主線: 使用者真正想達成什麼，哪些成立，哪些被證偽或修正
- AI 方案校準主線: AI 提了什麼方案，哪些被接受、修改、拒絕，原因是什麼

### Public Takeaway

One reusable sentence or short paragraph.
```

### Support Notes

Use these notes for checking and later editing. They do not need to appear as headings in the final article.

```markdown
#### 這次真正的問題

#### 原本的想法

#### 用戶意圖分析

成立的意圖:

修正後成立的意圖:

不成立或被放棄的意圖:

#### AI 方案如何被校準

被接受的部分:

被修改的部分:

被拒絕的部分:

#### 關鍵轉折

#### 最後形成的判斷

#### 留下來的教訓

#### 背景索引

#### 編輯錨點

Trigger line:

AI assumption:

Retained design:
```

## Event Card

Use event cards internally or include them when the user asks for transparent extraction evidence.

```yaml
event_id: "E01"
event_type: user_intent | ai_proposal | user_correction | decision | lesson | mistake | unresolved_question
conversation_fact: ""
interpretation: ""
evidence_excerpt: ""
thinking_tension: ""
background_anchors:
  issues: []
  prs: []
intent_status: established | modified_established | rejected | unresolved | not_applicable
ai_proposal_status: accepted | modified | rejected | not_applicable
public_value: high | medium | low
```

## Intent Analysis Item

```yaml
intent: ""
stated_or_inferred: stated | inferred
status: established | modified_established | rejected | unresolved
reason: ""
evidence_excerpt: ""
effect_on_article: ""
```

## AI Proposal Calibration Item

```yaml
proposal: ""
ai_assumption: ""
user_response: accepted | modified | rejected
reason: ""
resulting_adjustment: ""
lesson: ""
evidence_excerpt: ""
```

## Split Decision

Use this when one conversation milestone touches several related issues.

```yaml
candidate_group: ""
merge_reason: ""
split_risk: ""
final_decision: merge | split
why_this_preserves_the_thinking_arc: ""
```
