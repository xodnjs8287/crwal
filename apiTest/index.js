const express = require('express');
const http = require('http');
const path = require('path');
const { Server } = require("socket.io");

const app = express();
const server = http.createServer(app); // Express 앱으로 http 서버 생성
const io = new Server(server); // http 서버에 Socket.IO를 연결

// Koyeb 포트 또는 기본 8080 포트 사용
const port = process.env.PORT || 8080;

// 'public' 디렉토리의 정적 파일(index.html)을 서비스합니다.
app.use(express.static(path.join(__dirname, 'public')));

// 새로운 사용자가 접속했을 때의 처리
io.on('connection', (socket) => {
    console.log('✅ a user connected');

    // 사용자 접속을 모든 클라이언트에게 알림 (한글로 변경)
    io.emit('chat message', '데롱지가 입장했습니다.');

    // 사용자가 연결을 끊었을 때의 처리
    socket.on('disconnect', () => {
        console.log('❌ user disconnected');
        // 사용자 퇴장을 모든 클라이언트에게 알림 (한글로 변경)
        io.emit('chat message', '데롱지가 퇴장했습니다.');
    });

    // 'chat message' 이벤트를 수신했을 때의 처리
    socket.on('chat message', (msg) => {
        // 받은 메시지를 모든 클라이언트에게 다시 전송
        io.emit('chat message', msg);
        console.log('message: ' + msg);
    });
});

// http 서버를 실행합니다. (app.listen 대신 server.listen 사용)
server.listen(port, () => {
    console.log(`Chat server running on http://localhost:${port}`);
});