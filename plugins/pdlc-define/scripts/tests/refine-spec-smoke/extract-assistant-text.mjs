#!/usr/bin/env node
// Reads `claude -p --output-format stream-json --verbose` JSONL from stdin
// and writes the text content of every assistant message to stdout, in
// stream order.
//
// `--output-format text` (and the plain "final assistant message" reading
// tee'd output) only surfaces the last assistant message of a turn. When a
// turn emits protocol markers (CRITIC CAST, RESEARCHER DISPATCH, and so on)
// ahead of a tool call and then a different assistant message after the
// tool result comes back, those earlier markers never reach a text-mode
// transcript even though the session produced them. Reading the full
// stream-json event sequence and extracting every assistant text block
// fixes that: the transcript records what the model actually said, not only
// the last thing it said.
import { createInterface } from 'node:readline';

const rl = createInterface({ input: process.stdin, terminal: false });

rl.on('line', (line) => {
  const trimmed = line.trim();
  if (!trimmed) return;

  let event;
  try {
    event = JSON.parse(trimmed);
  } catch {
    return; // not a JSON event line; ignore rather than fail the turn
  }

  if (event.type !== 'assistant') return;
  const content = event.message && event.message.content;
  if (!Array.isArray(content)) return;

  for (const block of content) {
    if (block && block.type === 'text' && typeof block.text === 'string' && block.text.trim()) {
      process.stdout.write(`${block.text.trimEnd()}\n`);
    }
  }
});
