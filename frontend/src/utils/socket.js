/**
 * WebSocket utility for future real-time battle features.
 * This module will manage the WebSocket connection to the backend.
 */

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

class SocketManager {
  constructor() {
    this.socket = null;
    this.listeners = {};
  }

  connect(roomCode, token) {
    this.socket = new WebSocket(`${WS_URL}/${roomCode}?token=${token}`);

    this.socket.onopen = () => {
      console.log('[Socket] Connected to room:', roomCode);
      this._emit('connect');
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const { type, payload } = data;
        this._emit(type, payload);
      } catch (err) {
        console.error('[Socket] Failed to parse message:', err);
      }
    };

    this.socket.onclose = () => {
      console.log('[Socket] Disconnected');
      this._emit('disconnect');
    };

    this.socket.onerror = (err) => {
      console.error('[Socket] Error:', err);
      this._emit('error', err);
    };
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  send(type, payload) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type, payload }));
    }
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
    return () => this.off(event, callback); // returns unsubscribe fn
  }

  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter((cb) => cb !== callback);
    }
  }

  _emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach((cb) => cb(data));
    }
  }
}

export const socket = new SocketManager();

// Event types (future)
export const EVENTS = {
  JOIN_ROOM: 'join_room',
  LEAVE_ROOM: 'leave_room',
  START_GAME: 'start_game',
  UPDATE_STATE: 'update_state',
  PLAYER_READY: 'player_ready',
  GAME_OVER: 'game_over',
};

export default socket;
