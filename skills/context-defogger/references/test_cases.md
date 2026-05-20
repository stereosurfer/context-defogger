# Test Cases

These compact cases help calibrate extraction behavior. They are not public articles.

## Case 1: Handoff Mistaken For Public Log

Input pattern:

- User asks for a worklog skill that reads conversation and compares mentioned issues or PRs.
- AI proposes handoff-oriented output with GitHub status and operational sections.
- User corrects: the purpose is to publish the thinking online, not to hand off work.

Expected extraction:

- Central tension: "work record vs public thinking record"
- Public draft should start from the calibration insight, not from "the user asked for a skill."
- User intent:
  - "make a worklog skill" is modified_established
  - "create a handoff/status artifact" is rejected
  - "preserve thinking turns and lessons for public reading" is established
- AI proposal calibration:
  - handoff summary and live GitHub state are rejected or demoted
  - GitHub issues/PRs become background anchors
- Article split:
  - one article, because the correction is one coherent positioning shift
- Anti-pattern:
  - Do not output a long series of headings such as "成立的意圖 / 修正後成立的意圖 / 被拒絕的部分" as the article itself. Those are support notes.

## Case 2: Several PRs Share One Deeper Problem

Input pattern:

- Conversation mentions several issues/PRs.
- Each appears operationally different.
- User points out they all expose the same design mistake.

Expected extraction:

- Do not create one article per PR.
- Merge into one article if they share a central tension.
- Background anchors can list the issue/PR numbers, but body should explain the shared mistake.
- A split decision note should explain why time order or GitHub object boundaries were rejected.
- Public draft should make the shared mistake legible as an idea, not narrate each PR in order.

## Case 3: AI Proposal Rejected For Being Too Heavy

Input pattern:

- AI proposes a new layer, protocol, or system.
- User rejects it as too heavy and asks to reuse existing surfaces.
- Final direction becomes smaller and more repo-native.

Expected extraction:

- Central tension: "new abstraction vs reuse of existing control surface"
- User intent:
  - "solve the governance gap" is established
  - "add a new layer" is rejected unless the user asked for it
- AI proposal calibration:
  - rejected reason must name the user's reasoning, not just "user disliked it"
  - resulting adjustment should describe the smaller path
- Lesson:
  - a solution that adds control can still be wrong if it increases system weight without leverage
- Public draft should emphasize why the user's rejection improved the design, not just record that the AI proposal was rejected.

## Case 4: Initial Intent Does Not Survive Later Corrections

Input pattern:

- User asks for X.
- Through several corrections, the final target becomes Y.
- X remains historically important but should not define the final article.

Expected extraction:

- The article title and central tension should reflect Y, not X.
- X should appear in "original thought" or "rejected intent", not as the final thesis.
- The output should explicitly say which later correction changed the interpretation.
- Public draft should show how the later correction reinterpreted the whole conversation.

## Case 5: Three Currents Must Become Prose

Input pattern:

- User adds user-intent analysis and AI-proposal rejection analysis.
- AI responds with a strong paragraph explaining that the article becomes about calibration.
- A later template turns that insight into many checklist sections.
- User says the checklist feels like segmented summary and points to the paragraph as the desired style.

Expected extraction:

- Central tension: "structured extraction vs thesis-driven public writing"
- The three currents must be present:
  - problem current
  - user-intent current
  - AI-calibration current
- The public draft should include a connective thesis such as:
  - "人的意圖、AI 的提案、現實的限制，三者怎麼互相修正。"
- Support notes may still classify intent and proposal status, but the article embryo must read as prose.

## Case 6: One Milestone Becomes A Series

Input pattern:

- A conversation starts from one user need.
- The work naturally moves through several different thinking tensions.
- Each tension has a distinct lesson and title, but later tensions depend on earlier decisions.

Expected extraction:

- Use `series_mode: single_milestone_series`.
- Do not force the whole conversation into one long article.
- Do not split it into unrelated posts either.
- Each article needs its own central tension and public takeaway.
- The series summary should explain why the articles belong together.

## Case 7: Vague Analysis Must Become Concrete

Input pattern:

- Draft uses sentences such as "the user kept asking and made the AI proposal more precise" or "the proposal was calibrated into a conservative design."
- The conversation contains concrete user questions and concrete final design choices.

Expected extraction:

- Replace vague process claims with the actual questions the user asked.
- Replace "was calibrated" with the resulting design.
- Keep analysis-report tone if useful, but avoid empty connective phrases.
- Do not summarize away the user's correction when quoting or naming it would be clearer.
- Support notes should capture the trigger line, AI assumption, and retained design when the source makes them visible.
