const socket = io();

const form = document.getElementById("chatForm");
const input = document.getElementById("msgInput");
const messages = document.getElementById("messages");

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (text) {
    socket.emit("send_message", { text: text });
    input.value = "";
  }
});

socket.on("receive_message", (data) => {
  const el = document.createElement("div");
  el.classList.add("chat-message");
  el.classList.add(data.username === USERNAME ? "me" : "other");
  el.innerHTML = `<b>${data.username}:</b> ${data.text}`;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
});
