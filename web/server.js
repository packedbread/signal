let express = require('express');
let app = express();
let server = require('http').Server(app);
let io = require('socket.io')(server);
let timesync = require('timesync/server');

server.listen(80, () => console.log('Ready'));

app.use(express.static('public'));
app.use('/timesync', timesync.requestHandler);

const WINDOW = 500;

io.on('connection', (socket) => {
    socket.on('schedule-init', () => {
        console.log('SCHEDULE-INIT');
        io.clients((_, clients) => {
            let start = new Date().getTime() + 1000;
            let timestamp = start + WINDOW;
            console.log(socket.id);
            for (let client of clients) {
                let data = {timestamp: timestamp += WINDOW};
                if (client == socket.id) {
                    data = {
                        leader: true,
                        duration: clients.length * WINDOW + 2000,
                        timestamp: timestamp
                    };
                }
                console.log('SCHEDULE', client, data);
                io.to(client).emit('schedule', data);
            }
        });
    });
});
