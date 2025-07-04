const express = require('express');
const http = require('http');
const path = require('path');
const { Server } = require("socket.io");

const app = express();
const server = http.createServer(app);
const io = new Server(server);

const port = process.env.PORT || 8080;

app.use(express.static(path.join(__dirname, 'public')));

const foods = ["닭발", "햄버거", "치킨", "피자", "마라탕", "샹궈", "김치찜", "짬뽕", "깐풍기", "아구찜", "라면", "삼겹살", "족발", "보쌈", "떡볶이", "순대", "튀김", "파스타", "스테이크", "초밥", "돈까스", "짜장면", "탕수육", "양꼬치", "부대찌개", "감자탕", "제육덮밥", "냉면", "갈비찜", "순두부찌개", "김치볶음밥"];
const users = {}; // 접속한 사용자 정보를 저장할 객체

// --- 미니게임 상태 변수 ---
let numberGame = {
    isActive: false,
    answer: null
};

// --- 초성퀴즈 게임 상태 변수 ---
let choSungGame = {
    isActive: false,
    answer: null,
    question: null
};
// -----------------------------

// --- 한글 초성 추출 함수 ---
function getChoSung(word) {
    const cho = ["ㄱ","ㄲ","ㄴ","ㄷ","ㄸ","ㄹ","ㅁ","ㅂ","ㅃ","ㅅ","ㅆ","ㅇ","ㅈ","ㅉ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"];
    let result = "";
    for(let i=0; i<word.length; i++) {
        const code = word.charCodeAt(i) - 44032;
        if (code > -1 && code < 11172) {
            result += cho[Math.floor(code/588)];
        } else {
            result += word.charAt(i); // 한글이 아닐 경우 그대로 추가
        }
    }
    return result;
}
// -------------------------


io.on('connection', (socket) => {
    const randomFood = foods[Math.floor(Math.random() * foods.length)];
    users[socket.id] = `익명의 ${randomFood}`;
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

        // --- 게임 명령어 처리 ---
        if (msg.startsWith('/')) {
            if (msg === '/숫자게임') {
                if (numberGame.isActive || choSungGame.isActive) {
                    socket.emit('chat message', { type: 'system', text: '이미 다른 게임이 진행 중입니다.' });
                    return;
                }
                numberGame.isActive = true;
                numberGame.answer = Math.floor(Math.random() * 100) + 1;
                console.log(`🎮 Number game started! Answer: ${numberGame.answer}`);
                io.emit('chat message', { type: 'system', text: '🎲 숫자 맞추기 게임을 시작합니다! 1부터 100 사이의 숫자를 입력해주세요.' });
                return;
            }
            // 초성퀴즈 시작
            else if (msg === '/초성퀴즈') {
                if (numberGame.isActive || choSungGame.isActive) {
                    socket.emit('chat message', { type: 'system', text: '이미 다른 게임이 진행 중입니다.' });
                    return;
                }
                choSungGame.isActive = true;
                choSungGame.answer = foods[Math.floor(Math.random() * foods.length)];
                choSungGame.question = getChoSung(choSungGame.answer);
                console.log(`🎮 ChoSung game started! Answer: ${choSungGame.answer}`);
                io.emit('chat message', { type: 'system', text: `✍️ 초성퀴즈! 다음 단어를 맞혀보세요: [ ${choSungGame.question} ]` });
                return;
            }
        }

        // --- 숫자게임 로직 ---
        if (numberGame.isActive) {
            const guess = parseInt(msg, 10);
            if (!isNaN(guess)) {
                if (guess === numberGame.answer) {
                    io.emit('chat message', { type: 'system', text: `🎉 ${nickname}님이 정답(${numberGame.answer})을 맞췄습니다! 🎉` });
                    numberGame.isActive = false;
                } else if (guess < numberGame.answer) {
                    io.emit('chat message', { type: 'system', text: `[${nickname}] ${guess} -> UP! ⬆️` });
                } else {
                    io.emit('chat message', { type: 'system', text: `[${nickname}] ${guess} -> DOWN! ⬇️` });
                }
                return;
            }
        }

        // --- 초성퀴즈 로직 ---
        if (choSungGame.isActive) {
            if (msg === choSungGame.answer) {
                io.emit('chat message', { type: 'system', text: `🎉 ${nickname}님이 정답(${choSungGame.answer})을 맞췄습니다! 🎉` });
                choSungGame.isActive = false;
                choSungGame.answer = null;
                choSungGame.question = null;
                return;
            }
        }

        // --- 일반 채팅 메시지 처리 ---
        const messageData = {
            type: 'user',
            nickname: nickname,
            text: msg,
            socketId: socket.id
        };
        io.emit('chat message', messageData);
        console.log(`${nickname}: ${msg}`);
    });
});

server.listen(port, () => {
    console.log(`Chat server running on http://localhost:${port}`);
});