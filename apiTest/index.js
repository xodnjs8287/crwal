const express = require('express');
const path = require('path');

const app = express();

// Koyeb에서 제공하는 PORT 환경 변수를 사용하거나, 없을 경우 8080 포트를 사용합니다.
const port = process.env.PORT || 8080;

// 루트 경로 ('/')로 GET 요청이 오면 views/index.html 파일을 전송합니다.
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'views', 'index.html'));
});

// 서버를 시작하고, 어떤 포트에서 실행 중인지 콘솔에 출력합니다.
app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});