const socket = io();
const messagesDiv = document.getElementById('messages');
const msgInput = document.getElementById('msgInput');
const sendBtn = document.getElementById('sendBtn');

function addMessage(text, isMe = true) {
    let div = document.createElement('div');
    div.textContent = (isMe ? 'Я: ' : 'Друг: ') + text;
    div.style.background = isMe ? '#2a6b4e' : '#2c2c2c';
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}
sendBtn.onclick = () => {
    let text = msgInput.value;
    if(text) { socket.emit('send_message', {msg: text}); addMessage(text, true); msgInput.value = ''; }
};
socket.on('new_message', (data) => { addMessage(data.msg, false); });
// Видеокружки (WebRTC)
let mediaRecorder;
document.getElementById('recordVideo').onclick = async () => {
    let stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    mediaRecorder = new MediaRecorder(stream);
    let chunks = [];
    mediaRecorder.ondataavailable = e => chunks.push(e.data);
    mediaRecorder.onstop = () => {
        let blob = new Blob(chunks, {type: 'video/webm'});
        let file = new File([blob], "circle.webm");
        // Здесь отправь файл через fetch на сервер
        alert('Видеокружок записан, но нужно доработать отправку через /upload');
    };
    mediaRecorder.start();
    setTimeout(() => mediaRecorder.stop(), 5000);
};
// Стикеры
document.getElementById('stickerBtn').onclick = () => {
    let panel = document.getElementById('stickerPanel');
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
};
document.querySelectorAll('.sticker').forEach(btn => {
    btn.onclick = () => socket.emit('send_message', {msg: `[Стикер] ${btn.innerText}`});
});