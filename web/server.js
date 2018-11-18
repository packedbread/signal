let express = require('express');
let app = express();
let server = require('http').Server(app);
let io = require('socket.io')(server);
let timesync = require('timesync/server');
let cp = require('child_process');

server.listen(80, () => console.log('Ready'));

app.use(express.static('public'));
app.use('/timesync', timesync.requestHandler);

const before = 500;
const window = 250;
const after = 1000;

io.on('connection', (socket) => {
    socket.on('schedule-init', () => {
        console.log('SCHEDULE-INIT');
        io.clients((_, clients) => {
            let start = new Date().getTime() + before;
            let timestamp = start;
            let nodes = [];
            for (let client of clients) {
                if (client == socket.id) continue;
                timestamp += window;
                let data = {timestamp: timestamp};
                nodes.push(client);
                io.to(client).emit('schedule', data);
            }
            let data = {
                leader: true,
                duration: clients.length * window + before + after,
                timestamp: start,
                nodes: nodes
            };
            io.to(socket.id).emit('schedule', data);
        });
    });

    socket.on('sync-feedback', (data) => {
        console.log('FEEDBACK');
        let process = cp.spawn('python', ['detect.py']);
        process.stdout.setEncoding('utf8');
        process.stdout.on('data', output => {
            let beeps = JSON.parse(output);
            let starts = beeps.map(x => x[0]);
            let origin = starts.shift();
            if (starts.length == data.nodes.length) {
                starts = starts.map(x => x - origin);
                let offset = 0;
                for (let i = 0; i < starts.length; i++) {
                    offset += window;
                    let correction = offset - starts[i];
                    console.log('CALCULATED OFFSET:', correction);
                    io.to(data.nodes[i]).emit('sync-correction', {offset: -correction});
                }
            } else {
                console.log('ERROR: BAD NUMBER OF BEEPS');
            }
        });
        process.stdin.write(data.blob);
        process.stdin.end();
    });
});
