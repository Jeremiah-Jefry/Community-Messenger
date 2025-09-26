const socket = io();

const form = document.getElementById("chatForm");
const input = document.getElementById("msgInput");
const messages = document.getElementById("messages");

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (text) {
    // Escape HTML to prevent XSS (Good practice)
    const escapedText = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    socket.emit("send_message", { text: escapedText });
    input.value = "";
  }
});

socket.on("receive_message", (data) => {
  const el = document.createElement("div");
  el.classList.add("chat-message");
  
  // No longer needed to distinguish for styling, but keep for potential future features
  // el.classList.add(data.username === USERNAME ? "me" : "other"); 
  
  // Use a span for the username to allow for better CSS control
  const usernameSpan = document.createElement("b");
  usernameSpan.textContent = data.username;

  // Append username and message text
  el.appendChild(usernameSpan);
  el.append(data.text);
  
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
});