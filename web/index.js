let timesync = require('timesync');
let io = require('socket.io-client');
let $ = require('jquery');
let toto = require('./toto.mp3');
// import popper from "popper.js";
// import bootstrap from "bootstrap";

let sock = io.connect();
let ts = timesync.create({
    server: '/timesync',
    interval: 5000
});
let deviceOffset = 0;
let __oldNow = ts.now;
ts.now = () => __oldNow() + deviceOffset;

let blinkCard = $('#blink-card');
let syncBtn = $('#btn-sync');
let offsetSpan = $('#btn-offset span');
let playBtn = $('#btn-play');

// Get notified on changes in the offset
ts.on('change', offset => offsetSpan.text(offset.toFixed(1) + ' ms'));

// Blink
let blinkPeriod = 652;
let lastTime = 0;
setInterval(() => {
    if (ts.now() % blinkPeriod < lastTime) {
        if (ts.now() % (blinkPeriod * 2) < blinkPeriod) {
            blinkCard.removeClass('off');
        } else {
            blinkCard.addClass('off');
        }
    }
    lastTime = ts.now() % blinkPeriod;
}, 50);

// Init sync
syncBtn.on('click', () => {
    if (playerState) playBtn.click();
    syncBtn.addClass('disabled');
    playBtn.addClass('disabled');
    sock.emit('schedule-init');
});
sock.on('schedule', data => {
    console.log('SCHEDULE', data);
    if (data.leader) record(data.duration).then(chunks => sendRecord(chunks, data));
    if (playerState) playBtn.click();
    syncBtn.addClass('disabled');
    syncBtn.text('Syncing...');
    playBtn.addClass('disabled');
    let offset = data.timestamp - ts.now();
    beep(offset);
    setTimeout(() => {
        syncBtn.removeClass('disabled');
        syncBtn.text('Sync all');
        playBtn.removeClass('disabled');
    }, offset + 1000);
});
sock.on('sync-correction', data => {
    deviceOffset += data.offset;
    console.log('SET DEVICE CORRECTION:', deviceOffset);
});

// Audio sync
let context = new (window.AudioContext || window.webkitAudioContext)();

function beep(offset) {
    offset /= 1000;
    console.log('BEEP');
    let osc = context.createOscillator();
    osc.type = 'sine';
    osc.frequency.value = 900;
    osc.connect(context.destination);
    osc.start(context.currentTime + offset);
    osc.stop(context.currentTime + offset + 0.02);
    osc.onended = () => osc.disconnect(context.destination);
}

function record(duration) {
    console.log('RECORD');
    return new Promise((resolve) => {
        navigator.mediaDevices.getUserMedia({audio: true}).then(stream => {
            let mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            let audioChunks = [];
            mediaRecorder.addEventListener("dataavailable", event => audioChunks.push(event.data));
            setTimeout(() => {
                mediaRecorder.stop();
                stream.getTracks().forEach(track => track.stop());
                setTimeout(() => resolve(audioChunks), 500);
            }, duration);
            return audioChunks;
        });
    });
}

function sendRecord(chunks, data) {
    console.log('FEEDBACK');
    let fileReader = new FileReader();
    fileReader.onload = event => sock.emit('sync-feedback', {
        blob: event.target.result,
        nodes: data.nodes
    });
    fileReader.readAsArrayBuffer(chunks[0]);
}

// Player
let startOffset = 0 / 1000;
let playerState = false;
let buffer = null;
let duration = null;
let index = 0;
let nodes = [];

let gain = context.createGain();
gain.gain.value = 0;
gain.connect(context.destination);

let xhr = new XMLHttpRequest();
xhr.open('GET', toto, true);
xhr.responseType = 'arraybuffer';
xhr.onload = () => {
    context.decodeAudioData(xhr.response, buff => {
        buffer = buff;
        duration = Math.round((buffer.duration - startOffset) * 1000);
        for (let i = 0; i < 2; i++) {
            nodes[i] = context.createBufferSource();
            nodes[i].buffer = buffer;
            nodes[i].connect(gain);
        }
        let currentOffset = (ts.now() % duration) / 1000;
        nodes[1].start(0, startOffset + currentOffset);
        nodes[1].onended = () => setTimeout(playCycle, 500);
        playCycle();
    });
};
xhr.send();

function playCycle() {
    nodes[index] = context.createBufferSource();
    nodes[index].buffer = buffer;
    nodes[index].connect(gain);

    let nextOffset = (duration - ts.now() % duration) / 1000;
    console.log('Next start in:', nextOffset);
    let nextStart = nextOffset + context.currentTime;
    nodes[index].start(nextStart, startOffset);
    nodes[index].onended = () => setTimeout(playCycle, 500);

    index = +!index;
}

playBtn.on('click', () => {
    playerState = !playerState;
    playBtn.text(playerState ? 'Stop' : 'Play');
    gain.gain.value = +playerState;
});
