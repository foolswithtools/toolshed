# PLAYBOOK — default / tutorial

Last researched: 2026-04-28
Sources considered: AIR Media-Tech, 1of10, Humble&Brag, Section508.gov, Swarmify (WCAG guide), Teleprompter.com, OpusClip, Wave.video

## What this genre is for

A tutorial is a 16:9 video, typically 2–10 minutes long, that someone arrived at deliberately to learn a specific thing. The viewer has a problem and believes this video will solve it. Success looks like: the viewer finishes the section that answered their question, then either keeps watching for related material or leaves satisfied (the 2026 algorithm treats that "good abandonment" as a positive signal). Failure looks like: the viewer bounces in the first 30 seconds because the intro buried the promise, or fast-forwards through padding because the pacing dragged. The tutorial reader is patient enough to learn but impatient with throat-clearing — every second has to either teach or set up the next teaching beat.

## Decision overrides

`screencast-cut` reads these keys during Phase 3 planning. Each line is `key: value` followed by an inline `#`-prefixed justification. Do not invent keys outside this set.

- `intro_frames`: 45 # 1.5s wordmark flash AFTER the cold-open hook lands; long enough to register the brand, short enough that no one rewatches a 7s logo bumper
- `outro_frames`: 90 # 3s logo-card with a written next-step; gives the eye time to read one short line of text without dragging
- `cut_cadence_first_10s`: aggressive # the first 30s is where retention is won or lost; visual change every 1–2s while the hook lands
- `cut_cadence_steady_state`: calm # once committed, 25–40s holds let demonstrations breathe; cutting on every breath in the explanation phase looks frantic and hurts comprehension
- `caption_style`: band # learners read at their own pace and pause to re-read; a clean two-line band beats per-word reveal for accessibility and for technical terms that need to sit still
- `cta_shape`: next-steps # tutorials close with "now do X" — link to a follow-up video, a doc, or a concrete action — not a rhetorical question
- `max_duration_s`: 600 # 10 minutes is the soft ceiling for the educational sweet spot; surface a warning past this so the editor confirms the topic actually warrants the length

## Hook (first 3 seconds)

Open cold. No logo, no "hi everyone, today we're going to talk about" — those cost you the 20% of viewers who bail in the first 15 seconds. Lead with one of three shapes:

1. **Result-first.** Show the finished thing or the moment it works. ("This is the dashboard you're going to build" — and it's already on screen at frame 1.)
2. **Problem-first.** Name the specific pain the viewer arrived with. ("If your tests pass locally but fail in CI, it's almost always one of these three things.")
3. **Promise-first.** State the contract in one sentence. ("In four minutes you'll have a working webhook that survives restarts.")

Whichever shape you pick, deliver it inside three seconds, with the visual already in motion. The wordmark / brand bumper goes *after* this beat, not before — viewers will sit through 1.5s of branding once you've earned their attention, but not before.

A concrete good hook: open on the broken state (red error, failing test, ugly UI), hold for one beat, cut to the fixed state, voice-over names the technique. Total time: 4–6 seconds. The viewer now knows what they get, what's at stake, and that the video moves.

## Pacing

Treat the video as three pacing zones.

**Zone 1 — Hook + setup (0:00–0:30).** Cuts every 1–2 seconds. Minimum two visual changes (angle, zoom, b-roll, screen swap) inside the first ten seconds. This is the densest part of the video by design — you are buying the right to be calm later.

**Zone 2 — Main demonstration (0:30 to roughly two minutes before the end).** Settle into 20–40 second holds when a step is self-evidently moving on screen. Cut when the topic shifts, when the speaker's tone shifts, or when the screen has been static for more than ~25 seconds. Reset attention every 60–90 seconds with a visual change — angle swap, zoom-in on the relevant region, a callout overlay, or a quick cutaway to the result. Speak at 130–150 words per minute; faster reads as anxious, slower reads as padded.

**Idle gaps in source material.** Speed-ramp them out, don't cut to black. A four-second pause while something compiles becomes a 0.6s ramp with a subtle whoosh; the viewer registers that time passed without losing the thread. Hold the ramp at 4–6× when the gap is "waiting for a tool"; cut entirely if the gap is "the speaker lost their place."

**When to slow down.** At the moment of explanation that the whole video exists for. Stop cutting, hold the frame, let the voice carry it. Strategic silence — half a second between the setup and the punchline — builds gravity and makes the next cut feel earned.

**When to accelerate.** Recap montages, "and here are the other three variations" listings, anything the viewer has already seen the principle of. Fast cuts plus on-screen labels do the work without re-narrating.

## Captions

Use a two-line caption band, anchored in the lower third, white text on a translucent dark background. Maximum 42 characters per line, never more than two lines on screen at once. Sans-serif (Inter, Helvetica, or the profile's body face), 22–28 px equivalent at 1080p, with enough leading that descenders don't clip the band edge.

Captions stay on screen long enough to be read at a comfortable pace — roughly 160 words per minute of caption text, which usually means each caption holds for 1.5–4 seconds. Sync within ~250ms of the audio; the eye forgives a caption that arrives a hair early but not one that lags.

Punctuate naturally. Break lines on phrase boundaries, never mid-clause. When a technical term, command, or filename appears, give it its own beat — don't smear it across a line break. If the speaker is off-screen and could be confused with another voice (rare in tutorials but possible in panel-style content), prefix with the speaker's name once per turn.

Captions are not a transcript dump. Trim filler ("um", "you know", "kind of"), but do not paraphrase technical content — accuracy matters because viewers screenshot tutorials. Aim for 99%+ verbatim on anything that could be copy-pasted (commands, code, exact UI labels).

Karaoke per-word reveal is *off* by default for this genre. It pulls the eye to the moving word and away from whatever is being demonstrated, which is the opposite of what a tutorial wants. The override exists for profiles that lean into a more energetic, creator-personality feel; the default profile assumes accessibility-first.

## CTA / Outro

The outro is one structural beat: state the result, then state the next step. "You now have a working X. If you want to add Y, the link in the description goes there." Three to five seconds of voice over a logo-card with the next-step text written out, so a muted viewer can still act on it.

Do not stack CTAs. Pick one — the most important next action — and lean on it. "Subscribe and like and ring the bell and check the description" is noise. If subscription matters for this channel, the place for that ask is a quiet line at minute 1–2 ("if this is useful, subscribing means I keep making them"), not the outro.

The outro logo-card should be readable as a thumbnail — someone scrubbing the timeline lands on the last frame and should immediately see what to do next.

What does *not* belong in a tutorial outro: a question to the audience ("what should I cover next?"), a teaser for an unrelated video, a sponsor read (those go at minute 1 if at all), or a hard fade to black with no closing frame.

## Anti-patterns

- Opening with a logo bumper longer than 1.5 seconds before any content has appeared.
- Saying "in this video we're going to cover" instead of just covering it.
- Cutting on every sentence break in the explanation phase — it looks frantic and signals the editor didn't trust the content.
- Letting a static screen sit for more than ~25 seconds without a zoom, callout, or angle change.
- Using karaoke per-word captions during code or command demonstrations — the moving word steals attention from the thing being taught.
- Speed-ramping the moment the explanation actually lands; ramp the dead air, not the payload.
- Ending with a rhetorical question instead of a concrete next step.
- Stacking subscribe / like / comment / bell asks in the final ten seconds.
- Captions that paraphrase technical content; viewers screenshot tutorials and a wrong command in the captions becomes a bug report.
- Music that sits within 8 dB of the voice during explanation — it makes the viewer work to parse the words.

## Learnings

<!-- Appended over time via `screencast-cut` Phase 7. Each entry has date, video slug, rule, and why. Do not write entries here yourself — Learnings come from real videos the user has shipped. -->

_None yet._
