const socket = io();

const onlineUserList = document.getElementById("online-user-list");
const onlineUserCount = document.getElementById("online-user-count");

// GROUP_ID is defined in a <script> tag in chat.html
socket.on('connect', function () {
    socket.emit('join', { room: GROUP_ID });
});

const form = document.getElementById("chatForm");
const input = document.getElementById("msgInput");
const messages = document.getElementById("messages");

// Remove empty state when first message arrives
function removeEmptyState() {
    const emptyState = messages.querySelector('.chat-empty-state');
    if (emptyState) {
        emptyState.remove();
    }
}

// Get a deterministic hue class from a username
function getHueClass(username) {
    let hash = 0;
    for (let i = 0; i < username.length; i++) {
        hash = username.charCodeAt(i) + ((hash << 5) - hash);
    }
    return 'hue-' + ((Math.abs(hash) % 5) + 1);
}

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
    removeEmptyState();

    const msgRow = document.createElement("div");
    msgRow.classList.add("msg-row");
    msgRow.dataset.username = data.username;
    if (data.username === USERNAME) {
        msgRow.classList.add("msg-self");
    }

    // Avatar wrapper
    const avatarWrapper = document.createElement("div");
    avatarWrapper.classList.add("msg-avatar-wrapper");
    const avatar = document.createElement("div");
    avatar.classList.add("msg-avatar", getHueClass(data.username));
    avatar.textContent = data.username.charAt(0).toUpperCase();
    avatarWrapper.appendChild(avatar);

    // Body
    const body = document.createElement("div");
    body.classList.add("msg-body");

    // Author line
    const authorLine = document.createElement("div");
    authorLine.classList.add("msg-author-line");
    const authorName = document.createElement("span");
    authorName.classList.add("msg-author");
    authorName.textContent = data.username;
    const timeSpan = document.createElement("span");
    timeSpan.classList.add("msg-time");
    timeSpan.textContent = data.timestamp;
    authorLine.appendChild(authorName);
    authorLine.appendChild(timeSpan);

    // Text
    const textDiv = document.createElement("div");
    textDiv.classList.add("msg-text");
    textDiv.textContent = data.text;

    body.appendChild(authorLine);
    body.appendChild(textDiv);

    msgRow.appendChild(avatarWrapper);
    msgRow.appendChild(body);

    messages.appendChild(msgRow);
    messages.scrollTop = messages.scrollHeight;
});

socket.on("update_online_users", (data) => {
    onlineUserList.innerHTML = "";
    onlineUserCount.textContent = data.users.length;

    data.users.forEach(user => {
        const item = document.createElement("div");
        item.classList.add("member-item");
        if (user === USERNAME) {
            item.classList.add("is-you");
        }

        // Avatar
        const avatar = document.createElement("div");
        avatar.classList.add("member-avatar", getHueClass(user));
        avatar.textContent = user.charAt(0).toUpperCase();

        // Name
        const nameSpan = document.createElement("span");
        nameSpan.classList.add("member-name");
        nameSpan.textContent = user;

        item.appendChild(avatar);
        item.appendChild(nameSpan);

        // You tag
        if (user === USERNAME) {
            const youTag = document.createElement("span");
            youTag.classList.add("member-you-tag");
            youTag.textContent = "YOU";
            item.appendChild(youTag);
        }

        onlineUserList.appendChild(item);
    });
});

// Auto-scroll to the bottom on page load
window.addEventListener("load", () => {
    messages.scrollTop = messages.scrollHeight;
});