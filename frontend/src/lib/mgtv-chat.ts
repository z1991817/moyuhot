export type ChatRole = "system" | "user" | "assistant";

export type ChatMessageState = "done" | "streaming" | "error";

export interface ChatMessage {
  id: string;
  role: Exclude<ChatRole, "system">;
  content: string;
  createdAt: string;
  state?: ChatMessageState;
  errorMessage?: string;
}

export interface ChatThread {
  id: string;
  title: string;
  model: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
}

export interface ChatModelOption {
  value: string;
  label: string;
  description: string;
}

export const MGTV_CHAT_API_BASE = "/api/chat";
export const MGTV_CHAT_API_URL = `${MGTV_CHAT_API_BASE}/completions`;
export const MGTV_CHAT_MODELS_URL = `${MGTV_CHAT_API_BASE}/models`;
export const MGTV_CHAT_STORAGE_KEY = "moyu-ui-chat-history";
export const MGTV_CHAT_ACTIVE_KEY = "moyu-ui-chat-active-thread";
export const MGTV_CHAT_DEFAULT_MODEL = "fee/deepseek-v4-pro";
export const MGTV_CHAT_SYSTEM_PROMPT = "Please answer in concise, well-structured Markdown.";

export const MGTV_CHAT_MODELS: readonly ChatModelOption[] = [
  { value: "fee/deepseek-v4-pro", label: "DeepSeek V4 Pro", description: "FreeTheAI model" },
  { value: "fee/kimi-k2.6", label: "Kimi K2.6", description: "FreeTheAI model" },
  { value: "opc/qwen3.6-plus-free", label: "Qwen 3.6 Plus Free", description: "FreeTheAI model" },
  { value: "glm/glm-5", label: "GLM 5", description: "FreeTheAI model" },
  { value: "glm/glm-5.1", label: "GLM 5.1", description: "FreeTheAI model" },
  { value: "opc/minimax-m3-free", label: "MiniMax M3 Free", description: "FreeTheAI model" },
  { value: "bbl/gpt-5.4-mini", label: "GPT 5.4 Mini", description: "FreeTheAI model" },
] as const;

export function createId(prefix: string): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;
}

export function deriveThreadTitle(content: string): string {
  const normalized = content.replace(/\s+/g, " ").trim();
  if (!normalized) {
    return "New chat";
  }
  return normalized.length > 26 ? `${normalized.slice(0, 26)}...` : normalized;
}

export function createThread(model = MGTV_CHAT_DEFAULT_MODEL): ChatThread {
  const now = new Date().toISOString();
  return {
    id: createId("thread"),
    title: "New chat",
    model,
    createdAt: now,
    updatedAt: now,
    messages: [],
  };
}

export function createMessage(role: ChatMessage["role"], content: string): ChatMessage {
  return {
    id: createId(role),
    role,
    content,
    createdAt: new Date().toISOString(),
    state: "done",
  };
}

function isChatMessage(value: unknown): value is ChatMessage {
  if (!value || typeof value !== "object") {
    return false;
  }
  const candidate = value as Partial<ChatMessage>;
  return (
    (candidate.role === "user" || candidate.role === "assistant") &&
    typeof candidate.id === "string" &&
    typeof candidate.content === "string" &&
    typeof candidate.createdAt === "string"
  );
}

function isChatThread(value: unknown): value is ChatThread {
  if (!value || typeof value !== "object") {
    return false;
  }
  const candidate = value as Partial<ChatThread>;
  return (
    typeof candidate.id === "string" &&
    typeof candidate.title === "string" &&
    typeof candidate.model === "string" &&
    typeof candidate.createdAt === "string" &&
    typeof candidate.updatedAt === "string" &&
    Array.isArray(candidate.messages) &&
    candidate.messages.every(isChatMessage)
  );
}

export function parseStoredThreads(raw: string | null): ChatThread[] {
  if (!raw) {
    return [];
  }

  try {
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter(isChatThread).sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
  } catch {
    return [];
  }
}
