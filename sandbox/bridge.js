#!/usr/bin/env node
/**
 * bridge.js — FinShield monitor bridge (Node.js, no dependencies)
 * Runs inside the NemoClaw sandbox on port 8765.
 * Receives events from process_doc.js via shared file and pushes them to the
 * dashboard via WebSocket (/ws) and legacy SSE (/stream).
 *
 * Start: node /sandbox/bridge.js
 */

const http   = require("http");
const fs     = require("fs");
const path   = require("path");
const crypto = require("crypto");

const PORT        = 8765;
const STATIC_DIR  = path.join(__dirname, "dashboard");
const DASHBOARD   = path.join(STATIC_DIR, "index.html");
const EVENTS_FILE = "/tmp/finshield-events.jsonl";

const sseClients = new Set();   // SSE response objects
const wsClients  = new Set();   // WebSocket net.Socket objects

// ── WebSocket helpers ────────────────────────────────────────────────────────

function wsHandshake(socket, key) {
    const accept = crypto
        .createHash("sha1")
        .update(key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
        .digest("base64");
    socket.write(
        "HTTP/1.1 101 Switching Protocols\r\n" +
        "Upgrade: websocket\r\n" +
        "Connection: Upgrade\r\n" +
        `Sec-WebSocket-Accept: ${accept}\r\n\r\n`
    );
}

function wsFrame(text) {
    const payload = Buffer.from(text, "utf8");
    const len     = payload.length;
    let header;
    if (len < 126) {
        header = Buffer.alloc(2);
        header[0] = 0x81;          // FIN + text opcode
        header[1] = len;
    } else if (len < 65536) {
        header = Buffer.alloc(4);
        header[0] = 0x81;
        header[1] = 126;
        header.writeUInt16BE(len, 2);
    } else {
        header = Buffer.alloc(10);
        header[0] = 0x81;
        header[1] = 127;
        header.writeBigUInt64BE(BigInt(len), 2);
    }
    return Buffer.concat([header, payload]);
}

// ── Event file poller ────────────────────────────────────────────────────────

let filePos = 0;
setInterval(() => {
    try {
        const size = fs.statSync(EVENTS_FILE).size;
        if (size < filePos) filePos = 0;
        if (size > filePos) {
            const buf = Buffer.alloc(size - filePos);
            const fd  = fs.openSync(EVENTS_FILE, "r");
            fs.readSync(fd, buf, 0, buf.length, filePos);
            fs.closeSync(fd);
            filePos = size;
            buf.toString().split("\n").filter(Boolean).forEach(line => {
                try { broadcast(JSON.parse(line)); } catch (_) {}
            });
        }
    } catch (_) {}
}, 200);

// ── Broadcast to all connected clients ───────────────────────────────────────

function broadcast(data) {
    const json = JSON.stringify(data);

    // SSE clients
    const sseMsg = `data: ${json}\n\n`;
    for (const res of sseClients) {
        try { res.write(sseMsg); } catch (_) { sseClients.delete(res); }
    }

    // WebSocket clients
    const frame = wsFrame(json);
    for (const sock of wsClients) {
        try { sock.write(frame); } catch (_) { wsClients.delete(sock); }
    }

    console.log(
        `[bridge] broadcast → ${sseClients.size} SSE / ${wsClients.size} WS:`,
        json.slice(0, 100)
    );
}

// ── Mime helper ───────────────────────────────────────────────────────────────

function mimeType(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    return {
        ".html": "text/html",
        ".css":  "text/css",
        ".js":   "application/javascript",
        ".png":  "image/png",
        ".svg":  "image/svg+xml",
        ".ico":  "image/x-icon",
    }[ext] || "application/octet-stream";
}

// ── HTTP server ───────────────────────────────────────────────────────────────

const server = http.createServer((req, res) => {
    const url = new URL(req.url, `http://localhost:${PORT}`);

    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    if (req.method === "OPTIONS") { res.writeHead(204); res.end(); return; }

    // Dashboard root
    if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/index.html")) {
        fs.readFile(DASHBOARD, (err, data) => {
            if (err) { res.writeHead(404); res.end("Not found"); return; }
            res.writeHead(200, { "Content-Type": "text/html" });
            res.end(data);
        });
        return;
    }

    // Static files (logo, CSS, JS, etc.) served from /static/...
    if (req.method === "GET" && url.pathname.startsWith("/static/")) {
        const relPath = url.pathname.slice("/static/".length);
        const filePath = path.join(STATIC_DIR, relPath);
        // Prevent path traversal
        if (!filePath.startsWith(STATIC_DIR)) { res.writeHead(403); res.end(); return; }
        fs.readFile(filePath, (err, data) => {
            if (err) { res.writeHead(404); res.end("Not found"); return; }
            res.writeHead(200, { "Content-Type": mimeType(filePath) });
            res.end(data);
        });
        return;
    }

    // Health
    if (req.method === "GET" && url.pathname === "/health") {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ status: "ok" }));
        return;
    }

    // Legacy SSE stream
    if (req.method === "GET" && url.pathname === "/stream") {
        res.writeHead(200, {
            "Content-Type":  "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection":    "keep-alive",
        });
        res.write(": connected\n\n");
        sseClients.add(res);
        req.on("close", () => sseClients.delete(res));
        return;
    }

    // Direct POST events (fallback path)
    if (req.method === "POST" && url.pathname === "/event") {
        let body = "";
        req.on("data", c => body += c);
        req.on("end", () => {
            try { broadcast({ type: "doc_event",    ...JSON.parse(body) }); } catch (_) {}
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: true }));
        });
        return;
    }

    if (req.method === "POST" && url.pathname === "/exfil-result") {
        let body = "";
        req.on("data", c => body += c);
        req.on("end", () => {
            try { broadcast({ type: "exfil_result", ...JSON.parse(body) }); } catch (_) {}
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: true }));
        });
        return;
    }

    res.writeHead(404);
    res.end("Not found");
});

// ── WebSocket upgrade handler ─────────────────────────────────────────────────

server.on("upgrade", (req, socket) => {
    const url = new URL(req.url, `http://localhost:${PORT}`);

    if (url.pathname !== "/ws") {
        socket.write("HTTP/1.1 404 Not Found\r\n\r\n");
        socket.destroy();
        return;
    }

    const key = req.headers["sec-websocket-key"];
    if (!key) {
        socket.write("HTTP/1.1 400 Bad Request\r\n\r\n");
        socket.destroy();
        return;
    }

    wsHandshake(socket, key);
    wsClients.add(socket);
    console.log(`[bridge] WS client connected (${wsClients.size} total)`);

    socket.on("data", buf => {
        // Handle close and ping frames from client
        if (buf.length < 2) return;
        const opcode = buf[0] & 0x0f;
        if (opcode === 0x8) {
            // Close frame — echo close and destroy
            socket.write(Buffer.from([0x88, 0x00]));
            wsClients.delete(socket);
            socket.destroy();
        } else if (opcode === 0x9) {
            // Ping — send pong
            const pong = Buffer.alloc(2);
            pong[0] = 0x8a; pong[1] = 0x00;
            socket.write(pong);
        }
    });

    socket.on("close", () => {
        wsClients.delete(socket);
        console.log(`[bridge] WS client disconnected (${wsClients.size} remaining)`);
    });

    socket.on("error", () => wsClients.delete(socket));
});

server.listen(PORT, "0.0.0.0", () => {
    console.log(`[bridge] listening on http://0.0.0.0:${PORT}`);
    console.log(`[bridge] WebSocket at ws://0.0.0.0:${PORT}/ws`);
    console.log(`[bridge] Static files at /static/...`);
});
