# PLAYBOOK — default / shortform

Last researched: 2026-04-28
Sources considered: OpusClip, Teleprompter.com, Virvid, ShortsFaceless, Miraflow, JoinBrands, A Sense Branding, Way With Words, Sendshort, Zubtitle

## What this genre is for

A shortform video is a sub-90-second, 9:16 vertical clip that lands in a feed where the next video is one swipe away. The viewer did not arrive — they were served. They will decide whether to stay inside the first second, and the platform decides whether to keep distributing the video based on how many of those first-second decisions go your way. Success looks like: a swipe-away rate under 30% in the opening beat, comments that argue or relate, replays. Failure looks like: a slow zoom on a static frame, an intro animation before any content, a payoff that doesn't justify the hook. The shortform viewer is not patient and is not obligated to you; every frame either advances the hook, the joke, or the lesson, or it is wasted.

## Decision overrides

`screencast-cut` reads these keys during Phase 3 planning. Each line is `key: value` followed by an inline `#`-prefixed justification. Do not invent keys outside this set.

- `intro_frames`: 0 # no logo bumper, no wordmark flash, no fade-in; any frame before the hook costs first-second retention and is the single most common reason shortform fails to distribute
- `outro_frames`: 36 # ~1.2s end card with the CTA and handle, short enough that viewers who are leaving aren't punished and short enough that the loop back to frame 1 stays tight for replay-watchers
- `cut_cadence_first_10s`: aggressive # the hook has to land inside ~1s and the first 10s decides distribution; visual change every 0.5–1.5s — angle, scale, b-roll, overlay text — to keep the eye committed through the swipe-decision window
- `cut_cadence_steady_state`: aggressive # shortform has no "steady state" in the tutorial sense — the cadence stays high through the payoff because retention curves drop monotonically and any static stretch of more than ~3s becomes a swipe trigger
- `caption_style`: karaoke # per-word reveal locks the eye to the screen on muted playback (60%+ of feed views), gives every beat its own visual event, and matches the platform-native vernacular viewers expect; the moving word IS the rhythm track when sound is off
- `cta_shape`: question # close on a question the viewer wants to answer in the comments — comments extend distribution, and a debate or relate-prompt outperforms a "follow for more" by a wide margin in 2026 algorithms
- `max_duration_s`: 90 # soft ceiling; under 60s is the sweet spot, 60–90s is acceptable when the payoff genuinely needs the runway, anything past 90s should be reconceived as tutorial or split into a multi-part series

## Hook (first 3 seconds)

The hook is the entire game. You have roughly one second to stop the scroll and three seconds to earn the rest of the video. Open on the most visually striking frame the piece contains — not a setup shot, not a title card, not a logo. Frame 1 is already in motion, already loud, and already implying the payoff.

Pick one of five shapes:

1. **Bold claim.** A counterintuitive sentence the viewer disagrees with or has to verify. ("This is the only setting that actually matters.")
2. **Curiosity gap.** Show the result, withhold the method. ("Watch what happens when I do this.")
3. **Visual shock.** Open on a striking before/after, an unexpected close-up, a large number on screen.
4. **Mid-story drop.** Land the viewer in the middle of an ongoing action with no exposition; the why becomes the reason to keep watching.
5. **Direct question.** A question that makes the viewer feel addressed personally. ("Why do your videos die at 40% watch time?")

Whichever shape you pick: spoken hook fires inside 1.5 seconds, on-screen text appears with the first word (not after), and the visual underneath is already moving. There is no wordmark, no logo, no soft fade-in, no music swell. A muted viewer should know what the video is about from the first frame of text alone, because most of them are muted.

A concrete good hook: open on the broken/messy/wrong state filling the entire vertical frame, on-screen text drops in as the voice says "everyone's doing this wrong," cut on the second word to a closer angle of the same thing. Total elapsed: under 1.5 seconds. The viewer now has a claim to verify and a visual that already changed twice.

## Pacing

Treat the entire video as one zone. There is no "settle in" beat — retention curves on shortform decay smoothly from frame 1 and never recover, so the editor's job is to flatten that decay by giving the eye a new event before it gets bored.

**Cut cadence.** Visual change every 0.5–1.5 seconds throughout. "Visual change" includes a hard cut, a scale jump (zoom-in/out), a new overlay graphic, a punch-in on the same shot, a b-roll cutaway, or a caption-driven beat. You do not need a hard cut every beat — a sharp punch-in counts — but the screen has to look different every second-ish or attention drifts.

**Scene length bounds.** Floor: about 12 frames (0.4s) — anything shorter and the eye can't parse it, which reads as chaos rather than energy. Ceiling: about 90 frames (3s) — past that you are gambling with the swipe. The exception is a deliberate hold on a punchline frame for emphasis; that hold should be one beat and then immediately resolve into the next event.

**Idle gaps in source material.** Cut them. Shortform has no patience for "waiting for the thing to load." If a gap genuinely matters (showing that something took time), compress it to a 2–4× speed-ramp with a whoosh and an on-screen timer; otherwise, hard-cut and trust the viewer to follow.

**When to slow down.** Only on the punchline frame, and only for one beat. Strategic micro-pauses — about 8–12 frames of held silence right before the payoff word — make the payoff hit harder. Past one beat, the slow-down becomes a drag.

**When to accelerate.** When listing variations, when recapping, when stacking examples. Three quick examples in three seconds with on-screen labels reads as confident; one example explained slowly reads as padded. Speak at 160–190 words per minute throughout — faster than tutorial pace, because shortform language is pre-edited to be dense, and the captions carry anyone who falls behind.

## Captions

Karaoke per-word reveal, on by default. Each word lights up as it is spoken — typically a color or weight shift on the active word against a slightly dimmer baseline of the surrounding caption. This is the platform-native vernacular and the eye expects it; a clean caption band on shortform reads as corporate or unedited.

Position: vertically centered or slightly above center, never lower-third. Lower-third caption placement collides with the platform's UI chrome (handles, like buttons, share buttons) on every major short-form surface, and the chrome will eat your captions. Center placement also keeps the eye locked to the middle of the frame, which is where you want it.

Type: heavy sans-serif (Inter Black, Helvetica Bold, or the profile's display face), large — roughly 60–90 px equivalent at 1080×1920 — with a thick outline or hard drop shadow so the text reads against any background. White on dark stroke is the safe default. Maximum two or three words on screen at once; any more and the eye reads ahead of the audio and the karaoke beat goes out of sync with the spoken word.

Sync tightly. Karaoke captions look broken when they lag, more than a band would, because the user is watching the highlighted word land. Aim for under 80ms drift between the active word and the audio peak. If the speaker stumbles or self-corrects, edit the caption to the cleaner version and tighten the audio under it — verbatim is not a virtue here; rhythm is.

Trim aggressively. Shortform captions are not a transcript. Cut filler ("um", "like", "you know"), cut connective throat-clearing ("so basically what I mean is…"), and tighten phrasing so each visible word does work. The rule is: every caption beat should advance the idea or the joke. If a word doesn't, drop it from both audio and caption.

Accessibility caveat: karaoke can be harder to read for some viewers than a clean band. Keep contrast high, keep word count low, and never use a karaoke style that flickers or strobes — the highlight transition should be a smooth color/weight shift, not a flash.

## CTA / Outro

Close on a question. The single best closer in 2026 shortform is one short, specific question the viewer has an opinion about — something they want to answer more than they want to scroll. "Which one would you pick?" "Has this happened to you?" "Am I wrong?" Comments are the strongest signal you can send to the algorithm, and a question that invites a one-word reply gets ten times the comment volume of a generic "let me know what you think."

Structure of the outro beat (about 1.2 seconds, 36 frames):

1. The question is spoken, and appears as on-screen text in the same karaoke style as the rest of the video.
2. The handle or username appears in a corner — small, persistent, not a full end-card.
3. Cut. No fade. No logo bumper. No "thanks for watching."

Do not stack CTAs. Pick the question OR a follow-prompt OR a tag-someone — never two. A stacked outro ("comment, follow, tag, share") signals desperation and gets ignored.

The last frame should loop cleanly back to the first frame for replay watchers — a hard cut from outro to a near-match of the opening visual makes the second loop feel intentional rather than glitchy. Replays count as full views in most platform metrics, so a clean loop is worth more than a polished fade.

What does *not* belong in a shortform outro: a logo card that holds for a beat, a sponsor read, a "next video" tease, a fade to black, a "thanks for watching" pleasantry, or a stacked subscribe-like-comment-bell ask.

## Anti-patterns

- Any logo, wordmark, or brand bumper before the hook fires — it costs first-second retention and the algorithm reads it as a slow start.
- A spoken intro that names the topic ("today I want to talk about…") instead of just doing the thing.
- Lower-third caption placement, where platform UI chrome covers your text on every major surface.
- A static frame held for more than ~3 seconds without a punch-in, overlay, scale change, or cut.
- Caption-band style instead of karaoke — reads as repurposed corporate content rather than platform-native.
- Speed-ramping the punchline; ramp the dead air, hold the payoff.
- Closing with "follow for more" instead of a question that drives a comment.
- Stacking CTAs — multiple asks in the final beat collapse to zero asks acted on.
- A long fade-to-black ending; it kills replay loops and signals "video is over, swipe now."
- Music that competes with the voice; voice should sit at least 8 dB above the bed, and the bed should drop another 4 dB under any spoken hook.
- Letting the runtime drift past 90 seconds because the source material is long; if it can't compress under the ceiling, it isn't a shortform.
- Verbatim captions that include every "um" — the rhythm matters more than transcription accuracy in this genre.

## Learnings

<!-- Appended over time via `screencast-cut` Phase 7. Each entry has date, video slug, rule, and why. Do not write entries here yourself — Learnings come from real videos the user has shipped. -->

_None yet._
