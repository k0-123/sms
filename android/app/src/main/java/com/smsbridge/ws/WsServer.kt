package com.smsbridge.ws

import android.content.Context
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import org.java_websocket.WebSocket
import org.java_websocket.handshake.ClientHandshake
import org.java_websocket.server.WebSocketServer
import java.net.InetSocketAddress

const val WS_PORT = 8765

/** Embedded plain-ws:// server the desktop app connects to. See client.py's
 * NetworkClient docstring for why this isn't wss:// - the trust model relies
 * on the pairing code + on-device confirmation + long-lived token instead. */
class WsServer(private val context: Context) : WebSocketServer(InetSocketAddress(WS_PORT)) {
    val protocolHandler = ProtocolHandler(context)
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onOpen(conn: WebSocket, handshake: ClientHandshake) {
        Log.i("WsServer", "Client connected: ${conn.remoteSocketAddress}")
    }

    override fun onClose(conn: WebSocket, code: Int, reason: String, remote: Boolean) {
        protocolHandler.onClose(conn)
    }

    override fun onMessage(conn: WebSocket, message: String) {
        scope.launch {
            runCatching { protocolHandler.handle(message, conn) }
                .onFailure { Log.e("WsServer", "Error handling message", it) }
        }
    }

    override fun onError(conn: WebSocket?, ex: Exception) {
        Log.e("WsServer", "Server error", ex)
    }

    override fun onStart() {
        Log.i("WsServer", "Listening on port $WS_PORT")
    }

    fun shutdownServer() {
        runCatching { stop(1000) }
    }
}
