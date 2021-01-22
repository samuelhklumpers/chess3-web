const urlParams = new URLSearchParams(window.location.search);
const room = urlParams.get('room');
const mode = urlParams.get('mode');
const user = urlParams.get('user');

displayfield = document.querySelector("#playfield");
overfield = document.querySelector("#overlay");
statusbox = document.querySelector("#status");
playfield = [];
overlay = [];

function process(effect, args) {
    console.log(effect + " " + args.toString());

    if (effect === "draw_piece")
    {
        let [pos, shape, colour] = args;
        let [j, i] = pos;
        cell = playfield[i][j];
        cell.innerHTML = shape.fontcolor(colour);
    }
    else if (effect === "config")
    {
        let [key, value] = args;
        let [m, n] = value;

        if (key === "board_size") {
            createBoard(n, m);
        }
    }
    else if (effect === "status")
    {
        statusbox.innerHTML = args;
    }
    else if (effect === "overlay")
    {
        let [pos, text, colour] = args;
        let [j, i] = pos;
        cell = overlay[i][j];
        cell.innerHTML = text.fontcolor(colour);
    }
    else if (effect === "askstring")
    {
        let resp = prompt(args);
        socket.send(JSON.stringify(["write", resp]));
    }
}

socket = new WebSocket("ws://" + window.location.hostname + ":19684");
socket.onmessage = function (event) {
    let msg = event.data;
    let data = JSON.parse(msg);
    process(data[0], data[1]);
};
socket.onopen = function (_) {
    socket.send(JSON.stringify({"room": room, "mode": mode, "user": user}));
};

function createBoard(n, m) {
    for (let i = 0; i < n; i++) {
        let row = displayfield.insertRow(i);
        let orow = overfield.insertRow(i);
        playfield.push([]);
        overlay.push([]);
        for (let j = 0; j < m; j++) {
            let cell = row.insertCell(j);
            let ocell = orow.insertCell(j);


            if ((i + j) % 2 === 1)
                cell.className += " whitetile";
            else
                cell.className += " blacktile";

            cell.innerText = i.toString() + j.toString();

            cell.onclick = function (_) {
                socket.send(JSON.stringify(["click", [j, i]]));
            };

            overlay[i].push(ocell);
            playfield[i].push(cell);
        }
    }
}