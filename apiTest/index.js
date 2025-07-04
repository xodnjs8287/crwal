const express = require('express');
const http = require('http');
const path = require('path');
const { Server } = require("socket.io");

const app = express();
const server = http.createServer(app);
const io = new Server(server);

const port = process.env.PORT || 8080;

app.use(express.static(path.join(__dirname, 'public')));

const animals = ["사자", "호랑이", "코끼리", "기린", "하마", "판다", "펭귄", "고양이", "강아지", "돌고래"];
const users = {}; // 접속한 사용자 정보를 저장할 객체

// --- 미니게임 상태 변수 ---
let numberGame = {
    isActive: false,
    answer: null
};
// -------------------------

io.on('connection', (socket) => {
    const randomAnimal = animals[Math.floor(Math.random() * animals.length)];
    users[socket.id] = `익명의 ${randomAnimal}`;
    console.log(`✅ ${users[socket.id]} connected`);

    io.emit('chat message', {
        type: 'system',
        text: `${users[socket.id]}님이 입장했습니다.`
    });

    socket.on('disconnect', () => {
        const disconnectedUser = users[socket.id];
        if (disconnectedUser) {
            console.log(`❌ ${disconnectedUser} disconnected`);
            delete users[socket.id];
            io.emit('chat message', {
                type: 'system',
                text: `${disconnectedUser}님이 퇴장했습니다.`
            });
        }
    });

    socket.on('chat message', (msg) => {
        const nickname = users[socket.id];

        // --- 미니게임 로직 ---
        if (msg === '/숫자게임') {
            if (numberGame.isActive) {
                socket.emit('chat message', { type: 'system', text: '이미 숫자 맞추기 게임이 진행 중입니다.' });
                return;
            }
            numberGame.isActive = true;
            numberGame.answer = Math.floor(Math.random() * 100) + 1;
            console.log(`🎮 Number game started! Answer: ${numberGame.answer}`);
            io.emit('chat message', { type: 'system', text: '🎲 숫자 맞추기 게임을 시작합니다! 1부터 100 사이의 숫자를 입력해주세요.' });
            return;
        }

        if (numberGame.isActive) {
            const guess = parseInt(msg, 10);
            if (!isNaN(guess)) {
                if (guess === numberGame.answer) {
                    io.emit('chat message', { type: 'system', text: `🎉 ${nickname}님이 정답(${numberGame.answer})을 맞췄습니다! 🎉` });
                    numberGame.isActive = false;
                    numberGame.answer = null;
                } else if (guess < numberGame.answer) {
                    io.emit('chat message', { type: 'system', text: `${nickname}님의 숫자: ${guess} -> UP! ⬆️` });
                } else {
                    io.emit('chat message', { type: 'system', text: `${nickname}님의 숫자: ${guess} -> DOWN! ⬇️` });
                }
                return;
            }
        }
        // --- 미니게임 로직 끝 ---

        // 일반 채팅 메시지 처리
        const messageData = {
            type: 'user',
            nickname: nickname,
            text: msg,
            socketId: socket.id // 클라이언트로 보낸 사람의 ID를 함께 전송
        };
        io.emit('chat message', messageData);
        console.log(`${nickname}: ${msg}`);
    });
});

server.listen(port, () => {
    console.log(`Chat server running on http://localhost:${port}`);
});