package com.smsbridge

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.ListView
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.smsbridge.data.AppDatabase
import com.smsbridge.data.CallJobStatus
import com.smsbridge.data.JobStatus
import com.smsbridge.data.PairedDeviceEntity
import com.smsbridge.service.BridgeService
import com.smsbridge.ws.PairingManager
import com.smsbridge.ws.TokenStore
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {
    private lateinit var statusText: TextView
    private lateinit var ipAddressText: TextView
    private lateinit var pairingCodeText: TextView
    private lateinit var pairingHintText: TextView
    private lateinit var toggleButton: Button
    private lateinit var pendingText: TextView
    private lateinit var sentText: TextView
    private lateinit var callPendingText: TextView
    private lateinit var callSentText: TextView
    private lateinit var pairedDevicesList: ListView

    private var pairedDevices: List<PairedDeviceEntity> = emptyList()

    private val requestPermissionLauncher = registerForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.RequestMultiplePermissions()
    ) { results ->
        if (results[Manifest.permission.SEND_SMS] == true || results[Manifest.permission.CALL_PHONE] == true) {
            startBridge()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        statusText = findViewById(R.id.statusText)
        ipAddressText = findViewById(R.id.ipAddressText)
        pairingCodeText = findViewById(R.id.pairingCodeText)
        pairingHintText = findViewById(R.id.pairingHintText)
        toggleButton = findViewById(R.id.toggleServiceButton)
        pendingText = findViewById(R.id.pendingText)
        sentText = findViewById(R.id.sentText)
        callPendingText = findViewById(R.id.callPendingText)
        callSentText = findViewById(R.id.callSentText)
        pairedDevicesList = findViewById(R.id.pairedDevicesList)

        toggleButton.setOnClickListener {
            if (BridgeService.isRunning()) stopBridge() else requestPermissionsAndStart()
        }

        pairedDevicesList.setOnItemClickListener { _, _, position, _ ->
            val device = pairedDevices.getOrNull(position) ?: return@setOnItemClickListener
            AlertDialog.Builder(this)
                .setTitle("Revoke ${device.deviceName}?")
                .setMessage("This PC will need to be paired again before it can send SMS through this phone.")
                .setPositiveButton("Revoke") { _, _ -> revokeDevice(device.deviceId) }
                .setNegativeButton("Cancel", null)
                .show()
        }

        lifecycleScope.launch { refreshLoop() }
    }

    private fun requestPermissionsAndStart() {
        val permissions = mutableListOf(
            Manifest.permission.SEND_SMS,
            Manifest.permission.READ_PHONE_STATE,
            Manifest.permission.CALL_PHONE,
            Manifest.permission.READ_CALL_LOG,
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            permissions.add(Manifest.permission.ANSWER_PHONE_CALLS)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }
        val missing = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (missing.isEmpty()) {
            startBridge()
        } else {
            requestPermissionLauncher.launch(missing.toTypedArray())
        }
    }

    private fun startBridge() {
        val intent = Intent(this, BridgeService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
    }

    private fun stopBridge() {
        stopService(Intent(this, BridgeService::class.java))
    }

    private fun revokeDevice(deviceId: String) {
        lifecycleScope.launch {
            TokenStore(this@MainActivity).revoke(deviceId)
            AppDatabase.get(this@MainActivity).pairedDeviceDao().delete(deviceId)
        }
    }

    private suspend fun refreshLoop() {
        val jobDao = AppDatabase.get(this).jobDao()
        val callJobDao = AppDatabase.get(this).callJobDao()
        val deviceDao = AppDatabase.get(this).pairedDeviceDao()
        while (true) {
            val running = BridgeService.isRunning()
            toggleButton.text = if (running) "Stop Bridge" else "Start Bridge"
            statusText.text = if (running) "Status: 🟢 Running" else "Status: 🔴 Stopped"

            val ipStr = getActiveIpAddresses()
            ipAddressText.text = if (running) "IP: $ipStr:8765" else "IP: $ipStr (Bridge Stopped)"

            val code = PairingManager.currentCode()
            if (running && code != null) {
                pairingCodeText.text = code
                pairingCodeText.visibility = android.view.View.VISIBLE
                pairingHintText.visibility = android.view.View.VISIBLE
            } else {
                pairingCodeText.visibility = android.view.View.GONE
                pairingHintText.visibility = android.view.View.GONE
            }

            // SMS stats
            pendingText.text = "SMS Pending: ${jobDao.countByStatus(JobStatus.PENDING) + jobDao.countByStatus(JobStatus.SENDING)}"
            sentText.text = "SMS Sent: ${jobDao.countByStatus(JobStatus.SENT) + jobDao.countByStatus(JobStatus.DELIVERED)}"

            // Call stats
            val callPending = callJobDao.countByStatus(CallJobStatus.PENDING) + callJobDao.countByStatus(CallJobStatus.SENDING)
            val callCompleted = callJobDao.countByStatus(CallJobStatus.SENT) +
                                callJobDao.countByStatus(CallJobStatus.ANSWERED) +
                                callJobDao.countByStatus(CallJobStatus.NO_ANSWER)
            callPendingText.text = "Calls Queued: $callPending"
            callSentText.text = "Calls Done: $callCompleted"

            pairedDevices = deviceDao.listAll()
            pairedDevicesList.adapter = ArrayAdapter(
                this@MainActivity, android.R.layout.simple_list_item_1,
                pairedDevices.map { it.deviceName },
            )

            delay(2000)
        }
    }

    private fun getActiveIpAddresses(): String {
        return try {
            val ips = mutableListOf<String>()
            val interfaces = java.net.NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val iface = interfaces.nextElement()
                if (iface.isLoopback || !iface.isUp) continue
                val addrs = iface.inetAddresses
                while (addrs.hasMoreElements()) {
                    val addr = addrs.nextElement()
                    if (addr is java.net.Inet4Address && !addr.isLoopbackAddress) {
                        val host = addr.hostAddress ?: continue
                        if (!host.startsWith("127.")) {
                            ips.add(host)
                        }
                    }
                }
            }
            if (ips.isEmpty()) "No Network" else ips.first()
        } catch (e: Exception) {
            "Unknown"
        }
    }
}
