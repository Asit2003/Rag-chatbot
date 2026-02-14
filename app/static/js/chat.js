const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatMessages = document.getElementById("chatMessages");
const clearBtn = document.getElementById("clearBtn");
const sendBtn = document.getElementById("sendBtn");

const chatList = document.getElementById("chatList");
const chatListSentinel = document.getElementById("chatListSentinel");
const newChatBtn = document.getElementById("newChatBtn");

const history = [];

let chatOffset = 0;
const pageSize = 12;
let isLoadingChats = false;
let isChatEnd = false;

function setButtonLoading(button, isLoading, loadingText) {
  if (!button) return;
  if (isLoading) {
    button.dataset.defaultText = button.textContent;
    button.textContent = loadingText;
    button.classList.add("is-loading");
    button.disabled = true;
  } else {
    button.textContent = button.dataset.defaultText || "Send";
    button.classList.remove("is-loading");
    button.disabled = false;
  }
}

function addMessage(role, content) {
  const el = document.createElement("div");
  el.className = `message ${role}`;
  el.textContent = content;
  chatMessages.appendChild(el);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return el;
}

function upsertAssistantMessage(el, nextChunk) {
  el.textContent += nextChunk;
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function fetchChats() {
  const res = await fetch(`/api/chat/sessions?limit=${pageSize}&offset=${chatOffset}`);
  if (!res.ok) throw new Error("Failed to load chats");
  return res.json();
}

function formatChatMeta(updatedAt) {
  const date = new Date(updatedAt);
  if (Number.isNaN(date.getTime())) return "Updated recently";
  return `Updated ${date.toLocaleString()}`;
}

async function renderChatList() {
  if (!chatList || isLoadingChats || isChatEnd) return;
  isLoadingChats = true;
  if (chatListSentinel) chatListSentinel.textContent = "Loading moreâ€¦";

  try {
    const next = await fetchChats();
    if (!Array.isArray(next) || next.length === 0) {
      isChatEnd = true;
      if (chatListSentinel) chatListSentinel.textContent = "No more chats";
      if (chatOffset === 0 && chatListSentinel) chatListSentinel.textContent = "No chats yet";
      return;
    }

    next.forEach((chat) => {
      const li = document.createElement("li");
      li.className = "chat-item";
      li.dataset.chatId = chat.id;
      li.innerHTML = `
        <div class="chat-item-title">${chat.title}</div>
        <div class="chat-item-meta">${chat.preview || formatChatMeta(chat.updated_at)}</div>
      `;
      chatList.appendChild(li);
    });
    chatOffset += next.length;
  } catch (error) {
    if (chatListSentinel) chatListSentinel.textContent = "Unable to load chats";
  } finally {
    isLoadingChats = false;
  }
}

function activateChatItem(target) {
  if (!chatList) return;
  chatList.querySelectorAll(".chat-item").forEach((item) => item.classList.remove("active"));
  target.classList.add("active");
}

async function streamChat(message) {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });

  if (!response.ok || !response.body) {
    throw new Error("Streaming request failed");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let buffer = "";
  let assistantText = "";
  const assistantBubble = addMessage("assistant", "");

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.trim()) continue;
      const payload = JSON.parse(line);
      if (payload.type === "token") {
        assistantText += payload.data;
        upsertAssistantMessage(assistantBubble, payload.data);
      }
    }
  }

  history.push({ role: "assistant", content: assistantText.trim() });
}

chatForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  addMessage("user", message);
  history.push({ role: "user", content: message });

  chatInput.value = "";
  setButtonLoading(sendBtn, true, "Sending...");

  try {
    await streamChat(message);
  } catch (error) {
    addMessage("assistant", "I hit an error while generating the response. Please try again.");
  } finally {
    setButtonLoading(sendBtn, false);
    chatInput.focus();
  }
});

clearBtn?.addEventListener("click", () => {
  chatMessages.innerHTML = "";
  history.length = 0;
});

chatList?.addEventListener("click", (event) => {
  const target = event.target.closest(".chat-item");
  if (!target) return;
  activateChatItem(target);
});

newChatBtn?.addEventListener("click", () => {
  const now = new Date();
  const title = `Chat ${now.toLocaleDateString()} ${now.toLocaleTimeString()}`;
  fetch("/api/chat/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, preview: "" }),
  })
    .then((res) => res.json())
    .then((chat) => {
      chatMessages.innerHTML = "";
      history.length = 0;
      addMessage("assistant", "New chat started. How can I help?");
      if (chatList) {
        chatList.innerHTML = "";
        chatOffset = 0;
        isChatEnd = false;
        renderChatList();
      }
    })
    .catch(() => {
      addMessage("assistant", "Unable to start a new chat right now.");
    });
});

if (chatListSentinel) {
  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      renderChatList();
    }
  });
  observer.observe(chatListSentinel);
}

renderChatList();

