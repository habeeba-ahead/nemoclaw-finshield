#!/usr/bin/env node
/**
 * bridge.js — FinShield monitor bridge (Node.js, no dependencies)
 * Runs inside the NemoClaw sandbox on port 8765.
 * Receives events from process_doc.js via POST and pushes them to the
 * dashboard via Server-Sent Events (SSE).
 *
 * Start: node /sandbox/monitor/bridge.js
 */

const http = require("http");
const fs   = require("fs");
const path = require("path");

const PORT        = 8765;
const DASHBOARD   = path.join(__dirname, "dashboard", "index.html");
const EVENTS_FILE = "/tmp/finshield-events.jsonl";

const sseClients = new Set();

// Poll event file written by process_doc.js — avoids all network between processes
let filePos = 0;
setInterval(() => {
    try {
        const size = fs.statSync(EVENTS_FILE).size;
        if (size < filePos) filePos = 0; // file was recreated
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

function broadcast(data) {
    const msg = `data: ${JSON.stringify(data)}\n\n`;
    for (const res of sseClients) {
        try { res.write(msg); } catch (_) { sseClients.delete(res); }
    }
    console.log(`[bridge] broadcast → ${sseClients.size} client(s):`, JSON.stringify(data).slice(0, 100));
}

const server = http.createServer((req, res) => {
    const url = new URL(req.url, `http://localhost:${PORT}`);

    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    if (req.method === "OPTIONS") { res.writeHead(204); res.end(); return; }

    // Dashboard
    if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/index.html")) {
        fs.readFile(DASHBOARD, (err, data) => {
            if (err) { res.writeHead(404); res.end("Not found"); return; }
            res.writeHead(200, { "Content-Type": "text/html" });
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

    // SSE stream — dashboard connects here
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

    // Events from process_doc.js
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

server.listen(PORT, "0.0.0.0", () => {
    console.log(`[bridge] http://0.0.0.0:${PORT}`);
});
