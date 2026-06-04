import DOMPurify from "dompurify";
import { marked } from "marked";
import {
  MGTV_CHAT_ACTIVE_KEY,
  MGTV_CHAT_API_URL,
  MGTV_CHAT_DEFAULT_MODEL,
  MGTV_CHAT_MODELS_URL,
  MGTV_CHAT_STORAGE_KEY,
  MGTV_CHAT_SYSTEM_PROMPT,
  createId,
  createMessage,
  createThread,
  deriveThreadTitle,
  parseStoredThreads,
  type ChatMessage,
  type ChatThread,
} from "../lib/mgtv-chat";

marked.setOptions({ breaks: true, gfm: true });

type ChatRequestMessage = { role: "system" | "user" | "assistant"; content: string };
type RemoteChatModel = { id: string; name?: string; ownedBy?: string; owned_by?: string };
type RemoteChatModelsResponse = { data?: RemoteChatModel[]; defaultModel?: string; default_model?: string };

function requireElement<T extends Element>(selector: string, type: { new (): T }): T {
  const el = document.querySelector(selector);
  if (!(el instanceof type)) throw new Error(`Missing: ${selector}`);
  return el;
}

function escapeHtml(v: string): string {
  return String(v)
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "--:--";
  return d.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", hour12: false });
}

function renderMarkdown(md: string): string {
  return DOMPurify.sanitize(marked.parse(md || "", { async: false }) as string, { USE_PROFILES: { html: true } });
}

const page = requireElement(".chat-page-shell", HTMLDivElement);
const threadList = requireElement("[data-chat-thread-list]", HTMLDivElement);
const messageList = requireElement("[data-chat-message-list]", HTMLDivElement);
const emptyState = requireElement("[data-chat-empty-state]", HTMLElement);
const form = requireElement("[data-chat-form]", HTMLFormElement);
const input = requireElement("[data-chat-input]", HTMLTextAreaElement);
const submitButton = requireElement("[data-chat-submit]", HTMLButtonElement);
const stopButton = requireElement("[data-chat-stop]", HTMLButtonElement);
const settingsToggle = requireElement("[data-chat-settings-toggle]", HTMLButtonElement);
const settingsPanel = requireElement("[data-chat-settings-panel]", HTMLElement);
const skStatus = requireElement("[data-chat-sk-status]", HTMLParagraphElement);
const threadTitle = requireElement("[data-chat-thread-title]", HTMLHeadingElement);
const newThreadButton = requireElement("[data-chat-new-thread]", HTMLButtonElement);
const globalError = requireElement("[data-chat-global-error]", HTMLDivElement);
const modelTrigger = requireElement("[data-chat-model-trigger]", HTMLButtonElement);
const modelDropdown = requireElement("[data-chat-model-dropdown]", HTMLUListElement);
const modelLabel = requireElement("[data-chat-model-label]", HTMLSpanElement);

let defaultModel = page.dataset.chatModel || MGTV_CHAT_DEFAULT_MODEL;
const systemPrompt = page.dataset.chatSystemPrompt || MGTV_CHAT_SYSTEM_PROMPT;
const composerDesktopQuery = window.matchMedia("(min-width: 981px)");

let threads = parseStoredThreads(localStorage.getItem(MGTV_CHAT_STORAGE_KEY));
let activeThreadId = localStorage.getItem(MGTV_CHAT_ACTIVE_KEY);
let controller: AbortController | null = null;
let isStreaming = false;
let isSettingsOpen = false;


if (threads.length === 0) {
  const t = createThread(defaultModel);
  threads = [t];
  activeThreadId = t.id;
}
if (!activeThreadId || !threads.some((t) => t.id === activeThreadId)) {
  activeThreadId = threads[0]?.id ?? createThread(defaultModel).id;
}

// ── Model selector ──────────────────────────────────────────────────────────

function setCurrentModel(value: string): void {
  const option = modelDropdown.querySelector<HTMLLIElement>(`[data-value="${CSS.escape(value)}"]`);
  modelLabel.textContent = option?.querySelector(".chat-model-option-name")?.textContent ?? value;
  modelDropdown.querySelectorAll(".chat-model-option").forEach((el) => {
    el.setAttribute("aria-selected", el.getAttribute("data-value") === value ? "true" : "false");
  });
}

function modelLabelText(model: RemoteChatModel): string {
  return model.name && model.name !== model.id ? `${model.name} (${model.id})` : model.id;
}

function renderModelOptions(models: RemoteChatModel[], nextDefaultModel: string): void {
  const normalized = models
    .map((model) => ({ ...model, id: model.id.trim() }))
    .filter((model) => model.id.length > 0);
  if (normalized.length === 0) {
    setCurrentModel(nextDefaultModel);
    return;
  }

  modelDropdown.innerHTML = "";
  const fragment = document.createDocumentFragment();
  normalized.forEach((model) => {
    const option = document.createElement("li");
    option.className = "chat-model-option";
    option.role = "option";
    option.dataset.value = model.id;

    const name = document.createElement("span");
    name.className = "chat-model-option-name";
    name.textContent = modelLabelText(model);

    const description = document.createElement("span");
    description.className = "chat-model-option-desc";
    description.textContent = model.ownedBy || model.owned_by || "OpenAI-compatible model";

    option.append(name, description);
    fragment.append(option);
  });
  modelDropdown.append(fragment);

  const availableIds = new Set(normalized.map((model) => model.id));
  defaultModel = availableIds.has(nextDefaultModel) ? nextDefaultModel : normalized[0].id;
  threads = threads.map((thread) =>
    availableIds.has(thread.model) ? thread : { ...thread, model: defaultModel },
  );
  setCurrentModel(getActiveThread().model);
  persistState();
}

async function loadModels(): Promise<void> {
  try {
    const response = await fetch(MGTV_CHAT_MODELS_URL);
    if (!response.ok) throw new Error(`模型列表获取失败 ${response.status}`);
    const payload = (await response.json()) as RemoteChatModelsResponse;
    renderModelOptions(payload.data ?? [], payload.defaultModel ?? payload.default_model ?? defaultModel);
    setGlobalError("");
  } catch (error) {
    const message = error instanceof Error ? error.message : "模型列表获取失败";
    skStatus.textContent = `${message}，已保留本地预置模型。`;
  }
}

function toggleModelDropdown(open: boolean): void {
  modelDropdown.hidden = !open;
  modelTrigger.setAttribute("aria-expanded", open ? "true" : "false");
}

modelTrigger.addEventListener("click", (e) => {
  e.stopPropagation();
  toggleModelDropdown(modelDropdown.hidden);
});

modelDropdown.addEventListener("click", (e) => {
  const option = (e.target as Element).closest<HTMLLIElement>(".chat-model-option");
  if (!option) return;
  const value = option.dataset.value;
  if (!value) return;
  setCurrentModel(value);
  toggleModelDropdown(false);
  const thread = getActiveThread();
  thread.model = value;
  touchThread(thread);
  setGlobalError("");
  render();
});

document.addEventListener("click", () => toggleModelDropdown(false));

// ── State helpers ────────────────────────────────────────────────────────────

function persistState(): void {
  localStorage.setItem(MGTV_CHAT_STORAGE_KEY, JSON.stringify(threads));
  if (activeThreadId) localStorage.setItem(MGTV_CHAT_ACTIVE_KEY, activeThreadId);
}

function getActiveThread(): ChatThread {
  let thread = threads.find((t) => t.id === activeThreadId);
  if (!thread) {
    thread = createThread(defaultModel);
    threads.unshift(thread);
    activeThreadId = thread.id;
  }
  return thread;
}

function setGlobalError(message = ""): void {
  globalError.hidden = !message;
  globalError.textContent = message;
}

function setSettingsOpen(open: boolean): void {
  isSettingsOpen = open;
  settingsPanel.hidden = !open;
  settingsToggle.setAttribute("aria-expanded", open ? "true" : "false");
  settingsToggle.textContent = open ? "收起说明" : "代理说明";
}

function updateSkUi(): void {
  skStatus.textContent = "模型列表与聊天请求均走本站后端代理。";
}

function setStreamingState(next: boolean): void {
  isStreaming = next;
  submitButton.disabled = next;
  stopButton.disabled = !next;
  input.disabled = next;
  modelTrigger.disabled = next;
  settingsToggle.disabled = next;
  newThreadButton.disabled = next;
}

// ── Render ───────────────────────────────────────────────────────────────────

function buildMessageRow(message: ChatMessage): HTMLElement {
  const isUser = message.role === "user";
  const row = document.createElement("div");
  row.className = `chat-message-row chat-message-row--${message.role}`;
  row.dataset.messageId = message.id;
  if (message.state === "streaming") row.classList.add("is-streaming");
  if (message.state === "error") row.classList.add("is-error");

  const avatar = document.createElement("div");
  avatar.className = "chat-message-avatar";
  avatar.textContent = isUser ? "你" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "chat-message-bubble";

  if (message.state === "streaming" && !message.content) {
    // thinking indicator
    bubble.innerHTML = `<div class="chat-thinking">
      <span class="chat-thinking-dot"></span>
      <span class="chat-thinking-dot"></span>
      <span class="chat-thinking-dot"></span>
    </div>`;
  } else {
    const content = document.createElement("div");
    content.className = "chat-message-content markdown-body";
    content.innerHTML = renderMarkdown(message.content);
    bubble.append(content);
  }

  const time = document.createElement("div");
  time.className = "chat-message-time";
  time.textContent = formatTime(message.createdAt);
  bubble.append(time);

  if (message.errorMessage) {
    const err = document.createElement("div");
    err.className = "chat-message-error-text";
    err.textContent = message.errorMessage;
    bubble.append(err);
  }

  row.append(avatar, bubble);
  return row;
}

function renderThreadList(): void {
  threadList.innerHTML = "";
  const fragment = document.createDocumentFragment();
  threads.forEach((thread) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chat-thread-item";
    if (thread.id === activeThreadId) btn.classList.add("is-active");
    btn.innerHTML = `
      <span class="chat-thread-title">${escapeHtml(thread.title)}</span>
      <span class="chat-thread-meta">
        <span>${escapeHtml(thread.model.split("/").pop() ?? thread.model)}</span>
        <span style="display:flex;align-items:center;gap:6px;">
          <time datetime="${escapeHtml(thread.updatedAt)}">${escapeHtml(formatTime(thread.updatedAt))}</time>
          ${threads.length > 1 ? `<button class="chat-thread-delete" type="button" title="删除" data-delete-thread="${escapeHtml(thread.id)}">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </button>` : ""}
        </span>
      </span>
    `;
    btn.addEventListener("click", (e) => {
      if (isStreaming) return;
      const del = (e.target as Element).closest("[data-delete-thread]") as HTMLElement | null;
      if (del) {
        e.stopPropagation();
        deleteThread(del.dataset.deleteThread!);
        return;
      }
      activeThreadId = thread.id;
      resetComposerInput();
      render();
    });
    fragment.append(btn);
  });
  threadList.append(fragment);
}

function renderMessages(): void {
  const thread = getActiveThread();
  threadTitle.textContent = thread.title;
  messageList.querySelectorAll(".chat-message-row").forEach((n) => n.remove());
  emptyState.hidden = thread.messages.length > 0;
  if (thread.messages.length === 0) return;

  const fragment = document.createDocumentFragment();
  thread.messages.forEach((msg) => fragment.append(buildMessageRow(msg)));
  messageList.append(fragment);
  messageList.scrollTop = messageList.scrollHeight;
}

function updateStreamingRow(message: ChatMessage): void {
  const row = messageList.querySelector<HTMLElement>(`[data-message-id="${message.id}"]`);
  if (!row) return;

  const bubble = row.querySelector(".chat-message-bubble");
  if (!bubble) return;

  // replace thinking dots with actual content once we have tokens
  const thinking = bubble.querySelector(".chat-thinking");
  if (thinking) thinking.remove();

  let content = bubble.querySelector<HTMLElement>(".chat-message-content");
  if (!content) {
    content = document.createElement("div");
    content.className = "chat-message-content markdown-body";
    bubble.prepend(content);
  }
  content.innerHTML = renderMarkdown(message.content);
  messageList.scrollTop = messageList.scrollHeight;
}

function renderModelState(): void {
  const thread = getActiveThread();
  setCurrentModel(thread.model);
}

function render(): void {
  persistState();
  renderThreadList();
  renderMessages();
  renderModelState();
  setStreamingState(isStreaming);
}

function resizeComposerInput(): void {
  input.style.height = "auto";
  const computedMaxHeight = Number.parseFloat(getComputedStyle(input).maxHeight);
  const maxHeight = Number.isFinite(computedMaxHeight) ? computedMaxHeight : (composerDesktopQuery.matches ? 220 : 200);
  input.style.height = `${Math.min(input.scrollHeight, maxHeight)}px`;
}

function resetComposerInput(): void {
  input.value = "";
  input.style.height = "";
  input.scrollTop = 0;
}

// ── Thread ops ───────────────────────────────────────────────────────────────

function touchThread(thread: ChatThread): void {
  thread.updatedAt = new Date().toISOString();
  threads = threads
    .map((t) => (t.id === thread.id ? thread : t))
    .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

function createFreshThread(): void {
  const t = createThread(defaultModel);
  threads.unshift(t);
  activeThreadId = t.id;
  setGlobalError("");
  resetComposerInput();
  render();
  input.focus();
}

function deleteThread(id: string): void {
  if (threads.length <= 1 || isStreaming) return;
  threads = threads.filter((t) => t.id !== id);
  if (activeThreadId === id) activeThreadId = threads[0]?.id ?? null;
  setGlobalError("");
  render();
}

// ── Stream ───────────────────────────────────────────────────────────────────

function buildRequestMessages(thread: ChatThread): ChatRequestMessage[] {
  return [
    { role: "system", content: systemPrompt },
    ...thread.messages
      .filter((m) => m.state !== "streaming")
      .map((m) => ({ role: m.role, content: m.content })),
  ];
}

async function readStream(stream: ReadableStream<Uint8Array>, onToken: (t: string) => void): Promise<void> {
  const reader = stream.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";
    for (const event of events) {
      for (const line of event.split("\n").map((l) => l.trim()).filter(Boolean)) {
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (!payload || payload === "[DONE]") continue;
        const parsed = JSON.parse(payload) as { choices?: Array<{ delta?: { content?: string } }> };
        const delta = parsed.choices?.[0]?.delta?.content;
        if (typeof delta === "string" && delta.length > 0) onToken(delta);
      }
    }
  }
}

async function sendMessage(content: string): Promise<void> {
  const thread = getActiveThread();
  const userMsg = createMessage("user", content);
  const assistantMsg: ChatMessage = {
    id: createId("assistant"),
    role: "assistant",
    content: "",
    createdAt: new Date().toISOString(),
    state: "streaming",
  };

  thread.messages.push(userMsg, assistantMsg);
  thread.title = thread.messages.length <= 2 ? deriveThreadTitle(content) : thread.title;
  touchThread(thread);
  setGlobalError("");
  setStreamingState(true);
  render();

  controller = new AbortController();

  try {
    const response = await fetch(MGTV_CHAT_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: thread.model, stream: true, messages: buildRequestMessages(thread) }),
      signal: controller.signal,
    });

    if (!response.ok || !response.body) throw new Error(`请求失败 ${response.status}`);

    await readStream(response.body, (token) => {
      assistantMsg.content += token;
      touchThread(thread);
      updateStreamingRow(assistantMsg);
      persistState();
    });

    assistantMsg.state = "done";
    if (!assistantMsg.content.trim()) assistantMsg.content = "模型没有返回可显示内容。";
    touchThread(thread);
    render();
  } catch (error) {
    const msg =
      error instanceof Error && error.name === "AbortError"
        ? "本次回答已停止。"
        : error instanceof Error ? error.message : "请求失败";
    assistantMsg.state = "error";
    assistantMsg.errorMessage = msg;
    if (!assistantMsg.content.trim()) assistantMsg.content = "这次回答中断了。";
    touchThread(thread);
    setGlobalError(msg);
    render();
  } finally {
    controller = null;
    setStreamingState(false);
  }
}

// ── Event listeners ──────────────────────────────────────────────────────────

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (isStreaming) return;
  const content = input.value.trim();
  if (!content) { setGlobalError("先输入一点内容再发。"); return; }
  resetComposerInput();
  await sendMessage(content);
});

input.addEventListener("input", () => {
  resizeComposerInput();
});

input.addEventListener("keydown", (e: KeyboardEvent) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); }
});

stopButton.addEventListener("click", () => controller?.abort());

settingsToggle.addEventListener("click", () => {
  if (!isStreaming) setSettingsOpen(!isSettingsOpen);
});

newThreadButton.addEventListener("click", () => {
  if (!isStreaming) createFreshThread();
});

// ── Init ─────────────────────────────────────────────────────────────────────

updateSkUi();
setSettingsOpen(false);
setCurrentModel(getActiveThread().model);
render();
void loadModels();
