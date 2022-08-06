const urlParams = new URLSearchParams(window.location.search);
const room = urlParams.get('room');
const mode = urlParams.get('mode');
const user = urlParams.get('user');

displayfield = document.querySelector("#playfield");
overfield = document.querySelector("#overlay");
statusbox = document.querySelector("#status");
playfield = [];
overlay = [];

let width = 80;
let height = 80;
let dr = 80;


function toHTML(html) {
  let temp = document.createElement('template');
  html = html.trim();
  temp.innerHTML = html;
  return temp.content.firstChild;
}


function draw_svg(ix, raw, col) {
    let [i, j] = ix;
    let cell = playfield[i][j];
    let im = toHTML(raw);

    im.setAttribute("class", "square");
    im.setAttribute("fill", col);

    cell.innerHTML = "";
    cell.appendChild(im);
}


function draw_text(cell, shape, colour) {
    cell.innerHTML = "";
    cell.innerHTML = shape.fontcolor(colour);

    let children = cell.children;

    if (children.length > 0)
    {
        cell.removeChild(children[0]);
    }
}


let processWaitlist = Promise.resolve(0);

function process(effect, args) {
    console.log(effect + " " + args.toString());

    if (effect === "draw_piece")
    {
        let [pos, shape, colour] = args;
        let [j, i] = pos;

        let cell = playfield[i][j];

        if (shape.endsWith(".svg")) {
            let draw_callback = _ => fetch("/chess/images/" + shape).then(response => response.text()).then(raw => draw_svg([i, j], raw, colour));
            processWaitlist = processWaitlist.then(draw_callback);
        }
        else {
            let draw_callback = _ => draw_text(cell, shape, colour);
            processWaitlist = processWaitlist.then(draw_callback);
        }
    }
    else if (effect === "config")
    {
        let [key, value] = args;

        if (key === "board_size") {
            let [m, n] = value;
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

socket = new WebSocket("http://chess-v3.herokuapp.com/");
socket.onmessage = function (event) {
    let msg = event.data;
    let data = JSON.parse(msg);
    process(data[0], data[1]);
};
socket.onopen = function (_) {
    socket.send(JSON.stringify({"room": room, "mode": mode, "user": user}));
};


function createBoard(n, m) {
    let stylelink = document.querySelector("#stylesheet");
    let sheet = stylelink.sheet;
    let rules = sheet.rules;

    width = 80 / m;
    height = 80 / n;
    dr = Math.floor(Math.min(width, height));

    for (let i = 0; i < rules.length; ++i)
    {
        let rule = rules[i];
        if (rule.selectorText === "tr")
        {
            rule.style.height = dr.toString() + "vh";
        }
        else if (rule.selectorText === "td")
        {
            rule.style.width = dr.toString() + "vh";
        }
    }

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
