import { z } from 'zod';

export const ToolRequestSchema = z.object({
  type: z.literal('tool_request'),
  request_id: z.string().min(1),
  tool_name: z.string().min(1),
  args: z.record(z.string(), z.any()).optional().default({}),
});
export type ToolRequest = z.infer<typeof ToolRequestSchema>;

export const ToolResponseSchema = z.object({
  type: z.literal('tool_response'),
  request_id: z.string().min(1),
  approved: z.boolean(),
});
export type ToolResponse = z.infer<typeof ToolResponseSchema>;

export const MessageSchema = z.object({
  id: z.string().optional(),
  role: z.enum(['user', 'assistant', 'system']),
  content: z.string(),
  timestamp: z.string().optional(),
  emotion: z.string().optional(),
  attachments: z.array(z.string()).optional(),
});
export type ValidatedMessage = z.infer<typeof MessageSchema>;

export const SessionSchema = z.object({
  id: z.string().min(1),
  title: z.string().default('New Session'),
  updated_at: z.string().optional(),
  is_pinned: z.boolean().optional().default(false),
});
export type ValidatedSession = z.infer<typeof SessionSchema>;

export const SettingsSchema = z.object({
  model: z.string().optional(),
  temperature: z.number().min(0).max(2).optional(),
  theme: z.string().optional(),
  plugins: z.record(z.string(), z.any()).optional(),
}).passthrough();
export type ValidatedSettings = z.infer<typeof SettingsSchema>;
