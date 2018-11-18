import * as timesync from "timesync";
import * as io from "socket.io-client";
import $ from "jquery";
// import popper from "popper.js";
// import bootstrap from "bootstrap";

let sock = io.connect();
let ts = timesync.create({
    server: '/timesync',
    interval: 10000
});
let deviceOffset = 0;
let __oldNow = ts.now;
ts.now = () => __oldNow() + deviceOffset;

let blinkCard = $('#blink-card');
let syncBtn = $('#btn-sync');
let offsetSpan = $('#btn-offset span');

// Get notified on changes in the offset
ts.on('change', offset => offsetSpan.text(offset.toFixed(1) + ' ms'));

// Blink
let lastTime = 0;
setInterval(() => {
    if (ts.now() % 500 < lastTime) blinkCard.toggleClass('off');
    lastTime = ts.now() % 500;
}, 50);

// Init sync
syncBtn.on('click', () => sock.emit('schedule-init'));
sock.on('schedule', data => {
    console.log('SCHEDULE', data);
    if (data.leader) record(data.duration).then(chunks => sendRecord(chunks, data));
    beep(data.timestamp - ts.now());
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
