package com.smsbridge.service

import android.content.Context
import android.net.nsd.NsdManager
import android.net.nsd.NsdServiceInfo
import android.util.Log
import com.smsbridge.ws.WS_PORT

private const val SERVICE_TYPE = "_smsbridge._tcp."
private const val TAG = "NsdAdvertiser"

/** Advertises this phone on the local Wi-Fi network so the desktop app can
 * find it without the user typing an IP address. */
class NsdAdvertiser(private val context: Context) {
    private var nsdManager: NsdManager? = null
    private var registrationListener: NsdManager.RegistrationListener? = null

    fun start(deviceId: String, deviceName: String) {
        val manager = context.getSystemService(Context.NSD_SERVICE) as NsdManager
        nsdManager = manager

        val serviceInfo = NsdServiceInfo().apply {
            serviceName = "SMSBridge-${deviceId.take(8)}"
            serviceType = SERVICE_TYPE
            port = WS_PORT
            setAttribute("deviceId", deviceId)
            setAttribute("deviceName", deviceName)
            setAttribute("pairingRequired", "true")
        }

        val listener = object : NsdManager.RegistrationListener {
            override fun onServiceRegistered(info: NsdServiceInfo) {
                Log.i(TAG, "Registered as ${info.serviceName}")
            }

            override fun onRegistrationFailed(info: NsdServiceInfo, errorCode: Int) {
                Log.e(TAG, "Registration failed: $errorCode")
            }

            override fun onServiceUnregistered(info: NsdServiceInfo) {
                Log.i(TAG, "Unregistered")
            }

            override fun onUnregistrationFailed(info: NsdServiceInfo, errorCode: Int) {
                Log.e(TAG, "Unregistration failed: $errorCode")
            }
        }
        registrationListener = listener
        manager.registerService(serviceInfo, NsdManager.PROTOCOL_DNS_SD, listener)
    }

    fun stop() {
        registrationListener?.let { listener ->
            runCatching { nsdManager?.unregisterService(listener) }
        }
        registrationListener = null
    }
}
