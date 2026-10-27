import { describe, it, expect } from 'vitest';
// Import the REAL implementation (exported from ChatBubble) instead of
// re-declaring a copy — a local copy already drifted from production once.
import { sanitizeMarkdownContent } from '../components/ChatBubble';

describe('ChatBubble Markdown & Tag Sanitizer', () => {
  it('converts [STICKER:xxx] tags to markdown image syntax', () => {
    const input = 'Here is a sticker for you: [STICKER: happy_01]';
    const output = sanitizeMarkdownContent(input);
    expect(output).toContain('![sticker](/stickers/happy_01.png)');
  });

  it('normalizes malformed sticker URLs like /stickers/05_Crying_Comical. png', () => {
    const input = 'me started on that Thursday. ![mood](/stickers/05_Crying_Comical. png) But don\'t worry...';
    const output = sanitizeMarkdownContent(input);
    expect(output).toContain('![mood](/stickers/05_Crying_Comical.png)');
  });

  it('fixes missing exclamation marks in sticker links: [mood](/stickers/xxx.png)', () => {
    const input = 'Look at this [mood](/stickers/02_Happy.png)';
    const output = sanitizeMarkdownContent(input);
    expect(output).toContain('![mood](/stickers/02_Happy.png)');
  });

  it('strips <emotion>...</emotion> tags from output text', () => {
    const input = '<emotion>cheerful</emotion>Hello Master!';
    const output = sanitizeMarkdownContent(input);
    expect(output).toBe('Hello Master!');
  });

  it('handles empty or nullish strings safely', () => {
    expect(sanitizeMarkdownContent('')).toBe('');
  });

  it('preserves code blocks and mathematical expressions', () => {
    const input = 'Code block: ```python\nprint("hello")\n``` and formula: $x^2 + y^2 = z^2$';
    const output = sanitizeMarkdownContent(input);
    expect(output).toContain('print("hello")');
    expect(output).toContain('$x^2 + y^2 = z^2$');
  });

  it('strips <think>...</think> reasoning CONTENT, not just the tags', () => {
    const input = '<think>hidden chain of thought</think>Hello Master!';
    const output = sanitizeMarkdownContent(input);
    expect(output).toBe('Hello Master!');
    expect(output).not.toContain('hidden chain of thought');
    expect(output).not.toContain('<think>');
  });

  it('strips multi-line <thought> reasoning blocks', () => {
    const input = 'A<thought>step 1\nstep 2\nstep 3</thought>B';
    const output = sanitizeMarkdownContent(input);
    expect(output).toBe('AB');
    expect(output).not.toContain('step 2');
  });

  it('removes unclosed <emotion>/<think> tags without eating visible text', () => {
    const output = sanitizeMarkdownContent('<emotion>happy Hello <think>still here');
    expect(output).not.toContain('<emotion>');
    expect(output).not.toContain('<think>');
    expect(output).toContain('Hello');
  });

  it('never turns sticker/reasoning tags into images from stripped content', () => {
    const input = '<think>[STICKER:hidden_sticker]</think>Visible';
    const output = sanitizeMarkdownContent(input);
    expect(output).toBe('Visible');
    expect(output).not.toContain('/stickers/');
  });

  it('leaves raw javascript: image markdown untouched (react-markdown URL transform owns that)', () => {
    const input = '![x](javascript:alert(1))';
    const output = sanitizeMarkdownContent(input);
    // The sanitizer must not rewrite/mask URLs; react-markdown's
    // defaultUrlTransform strips non-http(s)/relative protocols later.
    expect(output).toBe(input);
    expect(output).not.toContain('/stickers/');
  });

  it('pins malicious sticker payloads to a relative /stickers/ path', () => {
    const output = sanitizeMarkdownContent('[STICKER: javascript:alert]');
    expect(output).toContain('![sticker](/stickers/javascript:alert.png)');
    // Must not produce a raw javascript: image destination.
    expect(output).not.toMatch(/!\[[^\]]*\]\(javascript:/);
  });

  it('adds the .png extension exactly once for sticker tags', () => {
    const output = sanitizeMarkdownContent('[STICKER: 02_Happy.png]');
    expect(output).toBe('![sticker](/stickers/02_Happy.png)');
    expect(output).not.toContain('.png.png');
  });

  it('trims surrounding whitespace from the final markdown', () => {
    expect(sanitizeMarkdownContent('  Hello  ')).toBe('Hello');
  });
});
