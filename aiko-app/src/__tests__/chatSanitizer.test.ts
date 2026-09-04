import { describe, it, expect } from 'vitest';

// Function under test (logic matching ChatBubble.tsx sanitizeMarkdownContent)
function sanitizeMarkdownContent(text: string): string {
  if (!text) return '';
  let cleaned = text.replace(/<emotion>.*?<\/emotion>/gi, '');
  cleaned = cleaned.replace(/\[STICKER\s*:\s*([^\]]+)\]/gi, (_, name) => {
    const cleanName = name.trim().endsWith('.png') ? name.trim() : `${name.trim()}.png`;
    return `![sticker](/stickers/${cleanName})`;
  });
  cleaned = cleaned.replace(/!\[(.*?)\]\(stickers\/(.*?)\)/gi, '![$1](/stickers/$2)');
  cleaned = cleaned.replace(/!\[\[STICKER\s*:\s*([^\]]+)\]\]\((.*?)\)/gi, '![$1]($2)');
  cleaned = cleaned.replace(/\\([*_`~[\]()])/g, '$1');
  cleaned = cleaned.replace(/!\[(.*?)\]\((.*?)\s+\.(png|jpg|jpeg|gif|webp)\)/gi, '![$1]($2.$3)');
  return cleaned.trim();
}

describe('ChatBubble Markdown & Tag Sanitizer', () => {
  it('converts [STICKER:xxx] tags to markdown image syntax', () => {
    const input = 'Here is a sticker for you: [STICKER: happy_01]';
    const output = sanitizeMarkdownContent(input);
    expect(output).toContain('![sticker](/stickers/happy_01.png)');
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
});
