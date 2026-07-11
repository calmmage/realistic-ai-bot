const conversation = document.querySelector("#conversation");
const messageForm = document.querySelector("#message-form");
const messageInput = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const timeJump = document.querySelector("#time-jump");
const offerForm = document.querySelector("#offer-form");
const offerInput = document.querySelector("#offer-input");
const offerButton = document.querySelector("#offer-button");
const resetButton = document.querySelector("#reset-button");
const typingTemplate = document.querySelector("#typing-template");

const params = new URLSearchParams(window.location.search);
const prefersReducedMotion = window.matchMedia(
  "(prefers-reduced-motion: reduce)",
).matches;
const pace =
  params.get("pace") === "fast" ? 0.06 : prefersReducedMotion ? 0.12 : 0.58;
let busy = false;

function sleep(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

async function request(path, body = {}) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Something went quiet.");
  }
  return payload;
}

function clockTime() {
  return new Intl.DateTimeFormat([], { hour: "2-digit", minute: "2-digit" })
    .format(new Date())
    .toLowerCase();
}

function addMessage(text, sender, testId = "") {
  const article = document.createElement("article");
  article.className = `message message-${sender}`;
  if (testId) article.dataset.testid = testId;

  const content = document.createElement("p");
  content.textContent = text;
  article.append(content);

  if (sender !== "system") {
    const time = document.createElement("time");
    time.textContent = clockTime();
    article.append(time);
  }

  conversation.append(article);
  conversation.scrollTop = conversation.scrollHeight;
  return article;
}

function setBusy(value) {
  busy = value;
  sendButton.disabled = value;
  timeJump.disabled = value;
  offerButton.disabled = value;
  document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.disabled = value;
  });
}

async function showPresence(message) {
  const presence = typingTemplate.content.firstElementChild.cloneNode(true);
  const label = presence.querySelector(".presence-label");
  label.textContent =
    message.presence === "thinking" ? "Mira is thinking" : "Mira is typing";
  conversation.append(presence);
  conversation.scrollTop = conversation.scrollHeight;
  await sleep(Math.max(90, message.pause_ms * pace));
  presence.remove();
}

async function playReply(payload) {
  setBusy(true);
  renderState(payload.state);
  for (const message of payload.messages) {
    await showPresence(message);
    addMessage(message.text, "bot", `${payload.kind}-message`);
  }
  setBusy(false);
  messageInput.focus();
}

async function sendMessage(text) {
  const cleaned = text.trim();
  if (!cleaned || busy) return;
  addMessage(cleaned, "user", "user-message");
  messageInput.value = "";
  resizeComposer();

  try {
    await playReply(await request("/api/message", { text: cleaned }));
  } catch (error) {
    addMessage(error.message, "system", "error-message");
    setBusy(false);
  }
}

function renderState(state) {
  document.querySelector("#profile-name").textContent = state.profile.name;
  document.querySelector("#profile-subtitle").textContent =
    state.profile.subtitle;
  document.querySelector("#profile-status").textContent = state.profile.status;
  document.querySelector("#profile-likes").textContent = state.profile.likes;
  document.querySelector("#profile-avoids").textContent = state.profile.avoids;
  document.querySelector("#turn-count").textContent =
    `${state.turns} ${state.turns === 1 ? "turn" : "turns"}`;

  const traits = document.querySelector("#traits");
  traits.replaceChildren(
    ...state.profile.traits.map((trait) => {
      const chip = document.createElement("span");
      chip.textContent = trait;
      return chip;
    }),
  );

  const interests = document.querySelector("#interest-list");
  interests.replaceChildren(
    ...state.interests.map((interest) => {
      const card = document.createElement("article");
      card.className = `interest${interest.core ? " core" : ""}`;
      card.dataset.testid = "interest";
      card.style.setProperty(
        "--affinity",
        `${Math.round(interest.affinity * 100)}%`,
      );

      const top = document.createElement("div");
      top.className = "interest-top";
      const name = document.createElement("span");
      name.className = "interest-name";
      name.textContent = interest.label;
      const badge = document.createElement("span");
      badge.className = "interest-badge";
      badge.textContent = interest.core ? "core" : "new";
      top.append(name, badge);

      const origin = document.createElement("p");
      origin.className = "interest-origin";
      origin.textContent = interest.origin;
      card.append(top, origin);
      return card;
    }),
  );

  const events = document.querySelector("#event-list");
  events.replaceChildren(
    ...state.events.map((event) => {
      const row = document.createElement("li");
      row.dataset.type = event.type;
      row.dataset.testid = "state-event";
      row.textContent = event.text;
      return row;
    }),
  );
}

function resizeComposer() {
  messageInput.style.height = "auto";
  messageInput.style.height = `${Math.min(messageInput.scrollHeight, 120)}px`;
}

messageForm.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(messageInput.value);
});

messageInput.addEventListener("input", resizeComposer);
messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    messageForm.requestSubmit();
  }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.prompt));
});

timeJump.addEventListener("click", async () => {
  if (busy) return;
  addMessage("three quiet hours later", "system");
  try {
    await playReply(await request("/api/proactive"));
  } catch (error) {
    addMessage(error.message, "system", "error-message");
    setBusy(false);
  }
});

offerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const topic = offerInput.value.trim();
  if (!topic || busy) return;
  offerInput.value = "";
  addMessage(`you offered Mira: ${topic}`, "system");
  try {
    await playReply(await request("/api/offer", { topic }));
  } catch (error) {
    addMessage(error.message, "system", "error-message");
    setBusy(false);
  }
});

resetButton.addEventListener("click", async () => {
  if (busy) return;
  const payload = await request("/api/reset");
  conversation.innerHTML = `
    <div class="day-marker"><span>tonight, again</span></div>
    <article class="message message-bot intro-message">
      <p>hey. i’m Mira.</p><time>now</time>
    </article>
    <article class="message message-bot intro-message">
      <p>new timeline. tell me what is on your mind.</p><time>now</time>
    </article>`;
  renderState(payload.state);
});

fetch("/api/state")
  .then((response) => response.json())
  .then(renderState)
  .catch(() =>
    addMessage(
      "The local demo server is not responding.",
      "system",
      "error-message",
    ),
  );
