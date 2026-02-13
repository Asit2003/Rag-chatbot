const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatMessages = document.getElementById("chatMessages");
const clearBtn = document.getElementById("clearBtn");
const sendBtn = document.getElementById("sendBtn");

const history = [];

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

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  addMessage("user", message);
  history.push({ role: "user", content: message });

  chatInput.value = "";
  sendBtn.disabled = true;

  try {
    await streamChat(message);
  } catch (error) {
    addMessage("assistant", "I hit an error while generating the response. Please try again.");
  } finally {
    sendBtn.disabled = false;
    chatInput.focus();
  }
});

clearBtn.addEventListener("click", () => {
  chatMessages.innerHTML = "";
  history.length = 0;
});
