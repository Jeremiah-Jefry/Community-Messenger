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
    const escapedText = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, ">");
    socket.emit("send_message", { text: escapedText, room: GROUP_ID });
    input.value = "";
    input.focus();
  }
});

socket.on("receive_message", (data) => {
    const messageWrapper = document.createElement("div");
    messageWrapper.classList.add("chat-message");
    if (data.username === USERNAME) {
        messageWrapper.classList.add("current-user");
    }

    const messageContent = document.createElement("div");
    messageContent.classList.add("message-content");

    const usernameDiv = document.createElement("div");
    usernameDiv.classList.add("username");
    usernameDiv.textContent = data.username;

    const textDiv = document.createElement("div");
    textDiv.textContent = data.text;

    const timestampDiv = document.createElement("div");
    timestampDiv.classList.add("timestamp", "text-end"); // Ensure text-end is applied
    timestampDiv.textContent = data.timestamp;

    messageContent.appendChild(usernameDiv);
    messageContent.appendChild(textDiv);
    messageContent.appendChild(timestampDiv);

    messageWrapper.appendChild(messageContent); // Only append messageContent

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