const socket = io();

const onlineUserList = document.getElementById("online-user-list");
const onlineUserCount = document.getElementById("online-user-count");

// GROUP_ID is defined in a <script> tag in chat.html
socket.on('connect', function() {
    socket.emit('join', {room: GROUP_ID});
});

const form = document.getElementById("chatForm");
const input = document.getElementById("msgInput");
const messages = document.getElementById("messages");

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (text) {
    const escapedText = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    socket.emit("send_message", { text: escapedText, room: GROUP_ID });
    input.value = "";
    input.focus();
  }
});

socket.on("receive_message", (data) => {
  const messageWrapper = document.createElement("div");
  messageWrapper.classList.add("chat-message");
  
  const timestampSpan = document.createElement("span");
  timestampSpan.classList.add("timestamp");
  timestampSpan.textContent = data.timestamp;

  const contentDiv = document.createElement("div");
  contentDiv.classList.add("content");
  
  const usernameSpan = document.createElement("b");
  usernameSpan.textContent = data.username;

  contentDiv.appendChild(usernameSpan);
  contentDiv.append(data.text);
  
  messageWrapper.appendChild(timestampSpan);
  messageWrapper.appendChild(contentDiv);
  
  messages.appendChild(messageWrapper);
  messages.scrollTop = messages.scrollHeight;
});

socket.on("update_online_users", (data) => {
    onlineUserList.innerHTML = "";
    onlineUserCount.textContent = data.users.length;
    
    data.users.forEach(user => {
        const li = document.createElement("li");
        li.classList.add("user-list-item");
        if (user === USERNAME) {
            li.innerHTML = `<b>${user} (You)</b>`;
        } else {
            li.textContent = user;
        }
        onlineUserList.appendChild(li);
    });
});