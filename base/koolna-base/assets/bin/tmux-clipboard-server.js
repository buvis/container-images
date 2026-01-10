#!/usr/bin/env node

const http = require('http');
const PORT = parseInt(process.env.TMUX_CLIPBOARD_PORT || '4040', 10);
const SESSION_LIST = (process.env.TMUX_CLIPBOARD_SESSIONS || 'manager,worker')
  .split(',')
  .map((item) => item.trim())
  .filter(Boolean);
const ALLOWED_SESSIONS = new Set(SESSION_LIST);

const CLIPBOARD_CHAR_LIMIT = parseInt(process.env.TMUX_CLIPBOARD_CHAR_LIMIT || '20000', 10);
const CLIPBOARD_BODY_LIMIT = parseInt(process.env.TMUX_CLIPBOARD_BODY_LIMIT || '65536', 10);
const CLIPBOARD_PING_INTERVAL_MS = 15000;

const clipboardState = new Map(); // session -> { text, seq, at }
const clipboardStreams = new Map(); // session -> Set<Client>
let clipboardSequence = 0;

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');

  if (req.method === 'GET' && url.pathname === '/healthz') {
    return respondJSON(res, 200, { status: 'ok', sessions: SESSION_LIST });
  }

  if (req.method === 'POST' && url.pathname === '/clipboard/push') {
    try {
      const contentType = (req.headers['content-type'] || '').toLowerCase();
      let session = url.searchParams.get('session');
      let text;

      if (contentType.includes('application/json')) {
        const payload = await readJSONBody(req, CLIPBOARD_BODY_LIMIT);
        session = session || payload.session;
        text = typeof payload.text === 'string' ? payload.text : null;
      } else {
        text = await readTextBody(req, CLIPBOARD_BODY_LIMIT);
      }

      if (!session || !ALLOWED_SESSIONS.has(session)) {
        return respondJSON(res, 400, { error: 'Unknown session' });
      }
      if (!text || typeof text !== 'string') {
        return respondJSON(res, 400, { error: 'Clipboard is empty' });
      }
      if (text.length > CLIPBOARD_CHAR_LIMIT) {
        return respondJSON(res, 400, {
          error: `Clipboard exceeds ${CLIPBOARD_CHAR_LIMIT.toLocaleString()} character limit`
        });
      }

      const normalizedText = normalizeNewlines(text);
      storeClipboardEntry(session, normalizedText);
      return respondJSON(res, 204, null);
    } catch (err) {
      const status = err instanceof SyntaxError ? 400 : 500;
      const message = err instanceof SyntaxError ? 'Invalid payload' : err.message;
      return respondJSON(res, status, { error: message });
    }
  }

  if (req.method === 'GET' && url.pathname === '/clipboard/latest') {
    const session = url.searchParams.get('session');
    const since = parseInt(url.searchParams.get('since') || '0', 10);
    if (!session || !ALLOWED_SESSIONS.has(session)) {
      return respondJSON(res, 400, { error: 'Unknown session' });
    }
    const entry = clipboardState.get(session);
    if (!entry || (Number.isFinite(since) && entry.seq <= since)) {
      addCors(res);
      res.writeHead(204);
      res.end();
      return;
    }
    return respondJSON(res, 200, entry);
  }

  if (req.method === 'GET' && url.pathname === '/clipboard/stream') {
    const session = url.searchParams.get('session');
    if (!session || !ALLOWED_SESSIONS.has(session)) {
      return respondJSON(res, 400, { error: 'Unknown session' });
    }
    startClipboardStream(session, req, res);
    return;
  }

  if (req.method === 'OPTIONS') {
    addCors(res);
    res.writeHead(204);
    res.end();
    return;
  }

  respondJSON(res, 404, { error: 'Not found' });
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`[clipboard] listening on http://127.0.0.1:${PORT}`);
});

function addCors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS, GET');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
}

function respondJSON(res, statusCode, body) {
  addCors(res);
  if (body === null) {
    res.writeHead(statusCode);
    res.end();
    return;
  }
  res.writeHead(statusCode, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(body));
}

function readJSONBody(req, limit = 1024) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', (chunk) => {
      data += chunk;
      if (data.length > limit) {
        reject(new Error('Payload too large'));
        req.destroy();
      }
    });
    req.on('end', () => {
      if (!data) {
        return reject(new SyntaxError('Empty body'));
      }
      try {
        const parsed = JSON.parse(data);
        resolve(parsed);
      } catch (err) {
        reject(err);
      }
    });
    req.on('error', reject);
  });
}

function readTextBody(req, limit = 1024) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.setEncoding('utf8');
    req.on('data', (chunk) => {
      data += chunk;
      if (data.length > limit) {
        reject(new Error('Payload too large'));
        req.destroy();
      }
    });
    req.on('end', () => {
      if (!data) {
        return reject(new SyntaxError('Empty body'));
      }
      resolve(data);
    });
    req.on('error', reject);
  });
}

function normalizeNewlines(text) {
  return text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
}

function storeClipboardEntry(session, text) {
  const entry = {
    session,
    text,
    seq: ++clipboardSequence,
    at: Date.now()
  };
  clipboardState.set(session, entry);
  broadcastClipboardEntry(entry);
}

function startClipboardStream(session, req, res) {
  addCors(res);
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    Connection: 'keep-alive',
    'X-Accel-Buffering': 'no'
  });
  res.write(':connected\n\n');

  const client = {
    res,
    session,
    heartbeat: setInterval(() => {
      try {
        res.write(':ping\n\n');
      } catch (err) {
        cleanup();
      }
    }, CLIPBOARD_PING_INTERVAL_MS)
  };

  const clients = ensureClientSet(session);
  clients.add(client);

  const cleanup = () => {
    if (!client.heartbeat) {
      return;
    }
    clearInterval(client.heartbeat);
    client.heartbeat = null;
    clients.delete(client);
    try {
      res.end();
    } catch (err) {
      // ignore
    }
  };

  req.on('close', cleanup);
  req.on('error', cleanup);

  const entry = clipboardState.get(session);
  if (entry) {
    sendClipboardEvent(client, entry);
  }
}

function ensureClientSet(session) {
  if (!clipboardStreams.has(session)) {
    clipboardStreams.set(session, new Set());
  }
  return clipboardStreams.get(session);
}

function broadcastClipboardEntry(entry) {
  const clients = clipboardStreams.get(entry.session);
  if (!clients || clients.size === 0) {
    return;
  }
  for (const client of clients) {
    sendClipboardEvent(client, entry);
  }
}

function sendClipboardEvent(client, entry) {
  try {
    client.res.write(`event: clipboard\n`);
    client.res.write(`data: ${JSON.stringify(entry)}\n\n`);
  } catch (err) {
    // drop later
  }
}
