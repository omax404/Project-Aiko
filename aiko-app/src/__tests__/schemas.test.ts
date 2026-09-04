import { describe, it, expect } from 'vitest';
import {
  ToolRequestSchema,
  ToolResponseSchema,
  MessageSchema,
  SessionSchema,
  SettingsSchema
} from '../schemas';

describe('Zod Schema Ingress Contracts', () => {
  it('validates a correct tool_request event', () => {
    const valid = {
      type: 'tool_request',
      request_id: 'req-12345',
      tool_name: 'OPEN',
      args: { target: 'notepad.exe' }
    };
    const result = ToolRequestSchema.safeParse(valid);
    expect(result.success).toBe(true);
  });

  it('rejects an invalid tool_request missing request_id', () => {
    const invalid = {
      type: 'tool_request',
      tool_name: 'OPEN'
    };
    const result = ToolRequestSchema.safeParse(invalid);
    expect(result.success).toBe(false);
  });

  it('validates a correct tool_response event', () => {
    const valid = {
      type: 'tool_response',
      request_id: 'req-12345',
      approved: true
    };
    const result = ToolResponseSchema.safeParse(valid);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.approved).toBe(true);
    }
  });

  it('validates message schemas with various roles', () => {
    const userMsg = MessageSchema.safeParse({
      role: 'user',
      content: 'Hello Aiko!'
    });
    expect(userMsg.success).toBe(true);

    const assistantMsg = MessageSchema.safeParse({
      role: 'assistant',
      content: 'Hello Master~',
      emotion: 'happy'
    });
    expect(assistantMsg.success).toBe(true);

    const invalidRole = MessageSchema.safeParse({
      role: 'attacker',
      content: 'Inject'
    });
    expect(invalidRole.success).toBe(false);
  });

  it('validates session schemas with defaults', () => {
    const res = SessionSchema.safeParse({
      id: 'session-abc'
    });
    expect(res.success).toBe(true);
    if (res.success) {
      expect(res.data.title).toBe('New Session');
      expect(res.data.is_pinned).toBe(false);
    }
  });

  it('validates settings schemas with temperature ranges', () => {
    const validSettings = SettingsSchema.safeParse({
      temperature: 0.7,
      theme: 'dark'
    });
    expect(validSettings.success).toBe(true);

    const invalidTemp = SettingsSchema.safeParse({
      temperature: 5.0
    });
    expect(invalidTemp.success).toBe(false);
  });
});
