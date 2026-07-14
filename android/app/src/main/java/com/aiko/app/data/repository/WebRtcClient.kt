package com.aiko.app.data.repository

import android.content.Context
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import org.webrtc.*
import java.nio.ByteBuffer

class WebRtcClient(
    context: Context,
    private val serverUrl: String,
    private val onMessageReceived: (String) -> Unit
) {
    // Prevent Context leak by keeping application context reference
    private val appContext = context.applicationContext

    // Structured coroutine lifecycle management
    private val job = SupervisorJob()
    private val clientScope = CoroutineScope(job + Dispatchers.IO)

    private var peerConnectionFactory: PeerConnectionFactory? = null
    private var peerConnection: PeerConnection? = null
    private var dataChannel: DataChannel? = null
    private val httpClient = OkHttpClient()
    @Volatile private var isConnecting = false

    private val _connectionState = MutableStateFlow(PeerConnection.PeerConnectionState.NEW)
    val connectionState: StateFlow<PeerConnection.PeerConnectionState> = _connectionState.asStateFlow()

    init {
        initializeWebRtc()
    }

    private fun initializeWebRtc() {
        try {
            // 1. Initialize PeerConnectionFactory using Application Context
            val initializationOptions = PeerConnectionFactory.InitializationOptions.builder(appContext)
                .createInitializationOptions()
            PeerConnectionFactory.initialize(initializationOptions)

            val options = PeerConnectionFactory.Options()
            peerConnectionFactory = PeerConnectionFactory.builder()
                .setOptions(options)
                .createPeerConnectionFactory()

            // 2. Configure ICE Servers
            val iceServers = listOf(
                PeerConnection.IceServer.builder("stun:stun.l.google.com:19302").createIceServer()
            )

            val rtcConfig = PeerConnection.RTCConfiguration(iceServers).apply {
                sdpSemantics = PeerConnection.SdpSemantics.UNIFIED_PLAN
                continualGatheringPolicy = PeerConnection.ContinualGatheringPolicy.GATHER_CONTINUALLY
            }

            // 3. Create PeerConnection
            val observer = object : PeerConnection.Observer {
                override fun onSignalingChange(state: PeerConnection.SignalingState?) {}
                override fun onIceConnectionChange(state: PeerConnection.IceConnectionState?) {}
                override fun onIceConnectionReceivingChange(receiving: Boolean) {}
                override fun onIceGatheringChange(state: PeerConnection.IceGatheringState?) {}
                override fun onIceCandidate(candidate: IceCandidate?) {}
                override fun onIceCandidatesRemoved(candidates: Array<out IceCandidate>?) {}
                override fun onAddStream(stream: MediaStream?) {}
                override fun onRemoveStream(stream: MediaStream?) {}
                
                override fun onDataChannel(dc: DataChannel?) {
                    if (dc != null) {
                        Log.i("WebRtcClient", "Received remote DataChannel setup")
                        // Clean up old local data channel if any to avoid leaks
                        dataChannel?.unregisterObserver()
                        dataChannel?.close()
                        dataChannel = dc
                        setupDataChannel(dc)
                    }
                }
                
                override fun onRenegotiationNeeded() {}
                override fun onAddTrack(receiver: RtpReceiver?, mediaStreams: Array<out MediaStream>?) {}
                
                override fun onConnectionChange(newState: PeerConnection.PeerConnectionState?) {
                    Log.i("WebRtcClient", "Connection state change: $newState")
                    if (newState != null) {
                        _connectionState.value = newState
                    }
                }
            }

            peerConnection = peerConnectionFactory?.createPeerConnection(rtcConfig, observer)

            // 4. Create local Data Channel
            val dcInit = DataChannel.Init().apply {
                ordered = true
            }
            dataChannel = peerConnection?.createDataChannel("chat", dcInit)
            setupDataChannel(dataChannel)

        } catch (e: Exception) {
            Log.e("WebRtcClient", "WebRTC initialization failed: ${e.message}")
            _connectionState.value = PeerConnection.PeerConnectionState.FAILED
        }
    }

    private fun setupDataChannel(dc: DataChannel?) {
        dc?.registerObserver(object : DataChannel.Observer {
            override fun onBufferedAmountChange(previousAmount: Long) {}
            override fun onStateChange() {
                Log.i("WebRtcClient", "Data Channel state: ${dc.state()}")
            }

            override fun onMessage(buffer: DataChannel.Buffer?) {
                if (buffer == null) return
                val data = ByteArray(buffer.data.remaining())
                buffer.data.get(data)
                val messageStr = String(data)
                onMessageReceived(messageStr)
            }
        })
    }

    /**
     * Start connection process: creates SDP offer, sends to server, and sets remote answer.
     */
    fun startConnection() {
        synchronized(this) {
            if (isConnecting) {
                Log.w("WebRtcClient", "Connection attempt already in progress, ignoring duplicate request.")
                return
            }
            isConnecting = true
        }

        clientScope.launch {
            try {
                val constraints = MediaConstraints().apply {
                    mandatory.add(MediaConstraints.KeyValuePair("OfferToReceiveAudio", "false"))
                    mandatory.add(MediaConstraints.KeyValuePair("OfferToReceiveVideo", "false"))
                }

                peerConnection?.createOffer(object : SdpObserver {
                    override fun onCreateSuccess(desc: SessionDescription?) {
                        if (desc == null) {
                            synchronized(this@WebRtcClient) { isConnecting = false }
                            return
                        }
                        peerConnection?.setLocalDescription(object : SdpObserver {
                            override fun onCreateSuccess(p0: SessionDescription?) {}
                            override fun onSetSuccess() {
                                clientScope.launch {
                                    try {
                                        sendOfferToServer(desc)
                                    } finally {
                                        synchronized(this@WebRtcClient) { isConnecting = false }
                                    }
                                }
                            }
                            override fun onCreateFailure(p0: String?) {
                                synchronized(this@WebRtcClient) { isConnecting = false }
                            }
                            override fun onSetFailure(p0: String?) {
                                synchronized(this@WebRtcClient) { isConnecting = false }
                            }
                        }, desc)
                    }

                    override fun onSetSuccess() {}
                    override fun onCreateFailure(error: String?) {
                        Log.e("WebRtcClient", "SDP Offer creation failed: $error")
                        synchronized(this@WebRtcClient) { isConnecting = false }
                    }
                    override fun onSetFailure(error: String?) {}
                }, constraints)
            } catch (e: Exception) {
                Log.e("WebRtcClient", "Error starting connection: ${e.message}")
                synchronized(this@WebRtcClient) { isConnecting = false }
            }
        }
    }

    private fun sendOfferToServer(offerDesc: SessionDescription) {
        val payload = JSONObject().apply {
            put("sdp", offerDesc.description)
            put("type", offerDesc.type.canonicalForm())
        }

        val requestUrl = if (serverUrl.endsWith("/")) {
            "${serverUrl}api/webrtc/offer"
        } else {
            "${serverUrl}/api/webrtc/offer"
        }

        val requestBody = payload.toString().toRequestBody("application/json".toMediaTypeOrNull())
        val request = Request.Builder()
            .url(requestUrl)
            .post(requestBody)
            .build()

        try {
            // Guarantee that HTTP response bodies are safely closed
            httpClient.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val responseBody = response.body?.string() ?: ""
                    val json = JSONObject(responseBody)
                    val answerSdp = json.optString("sdp")
                    val answerType = json.optString("type", "answer")

                    if (answerSdp.isNotEmpty()) {
                        val remoteDesc = SessionDescription(
                            SessionDescription.Type.fromCanonicalForm(answerType),
                            answerSdp
                        )
                        setRemoteDescription(remoteDesc)
                    }
                } else {
                    Log.e("WebRtcClient", "Server SDP exchange failed with status: ${response.code}")
                }
            }
        } catch (e: Exception) {
            Log.e("WebRtcClient", "SDP exchange network error: ${e.message}")
        }
    }

    private fun setRemoteDescription(remoteDesc: SessionDescription) {
        peerConnection?.setRemoteDescription(object : SdpObserver {
            override fun onCreateSuccess(p0: SessionDescription?) {}
            override fun onSetSuccess() {
                Log.i("WebRtcClient", "Remote SDP answer set successfully.")
            }
            override fun onCreateFailure(p0: String?) {}
            override fun onSetFailure(error: String?) {
                Log.e("WebRtcClient", "Remote SDP answer set failure: $error")
            }
        }, remoteDesc)
    }

    /**
     * Send message over WebRTC data channel.
     */
    fun sendMessage(msg: String): Boolean {
        val dc = dataChannel
        if (dc != null && dc.state() == DataChannel.State.OPEN) {
            val buffer = ByteBuffer.wrap(msg.toByteArray())
            return dc.send(DataChannel.Buffer(buffer, false))
        }
        return false
    }

    /**
     * Terminate the client scope, unregister observers, and release WebRTC native objects.
     */
    fun close() {
        try {
            job.cancel() // Cancel all pending coroutines running inside clientScope
            
            dataChannel?.unregisterObserver()
            dataChannel?.close()
            dataChannel = null

            peerConnection?.close()
            peerConnection?.dispose()
            peerConnection = null

            peerConnectionFactory?.dispose()
            peerConnectionFactory = null
        } catch (e: Exception) {
            Log.e("WebRtcClient", "Close failed: ${e.message}")
        }
    }
}
