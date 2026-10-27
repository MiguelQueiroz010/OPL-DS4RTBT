// Experimental sample (untested): phone as a PS2 steering wheel. Needs API 28+, BLUETOOTH_CONNECT permission.
// Pair the phone with the PS2 dongle first, then call connect(device). See docs/MOTIONPAD.md.
package motionpad

import android.bluetooth.*
import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import java.util.concurrent.Executors
import kotlin.math.*

class MotionPadService(private val ctx: Context) : SensorEventListener {
    private val descriptor = byteArrayOf(
        0x05, 0x01, 0x09, 0x05, 0xA1.toByte(), 0x01,          // Gamepad
        0x85.toByte(), 0x01,                                    //   Report ID 1
        0x15, 0x00, 0x26, 0xFF.toByte(), 0x00, 0x75, 0x08,      //   0..255, 8 bit
        0x09, 0x30, 0x09, 0x32, 0x09, 0x35, 0x95.toByte(), 0x03, //   X (steer), Z (throttle), Rz (brake)
        0x81.toByte(), 0x02,
        0x05, 0x09, 0x19, 0x01, 0x29, 0x08, 0x25, 0x01,          //   8 buttons
        0x75, 0x01, 0x95.toByte(), 0x08, 0x81.toByte(), 0x02,
        0xC0.toByte())

    private var hid: BluetoothHidDevice? = null
    private var host: BluetoothDevice? = null
    private var btn = 0
    private val report = ByteArray(4)
    private val sm = ctx.getSystemService(Context.SENSOR_SERVICE) as SensorManager

    fun start() {
        val adapter = (ctx.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager).adapter
        adapter.getProfileProxy(ctx, object : BluetoothProfile.ServiceListener {
            override fun onServiceConnected(p: Int, proxy: BluetoothProfile) {
                hid = proxy as BluetoothHidDevice
                hid!!.registerApp(
                    BluetoothHidDeviceAppSdpSettings("MotionPad", "PS2 wheel", "OPL",
                        BluetoothHidDevice.SUBCLASS1_COMBO, descriptor),
                    null, null, Executors.newSingleThreadExecutor(),
                    object : BluetoothHidDevice.Callback() {})
            }
            override fun onServiceDisconnected(p: Int) { hid = null }
        }, BluetoothProfile.HID_DEVICE)
        sm.registerListener(this, sm.getDefaultSensor(Sensor.TYPE_GRAVITY), SensorManager.SENSOR_DELAY_GAME)
    }

    fun connect(d: BluetoothDevice) { host = d; hid?.connect(d) }
    fun setButtons(triangle: Boolean, circle: Boolean) { btn = (if (triangle) 1 else 0) or (if (circle) 2 else 0) }

    override fun onSensorChanged(e: SensorEvent) {
        val (gx, gy, gz) = Triple(e.values[0], e.values[1], e.values[2])
        // Landscape, phone held like a wheel: roll = steering, pitch = throttle (forward) / brake (back)
        val roll = Math.toDegrees(atan2(gy.toDouble(), gx.toDouble().let { if (it == 0.0) 1e-6 else it }) - PI / 2)
        val pitch = Math.toDegrees(atan2(gz.toDouble(), sqrt((gx * gx + gy * gy).toDouble())))
        val steer = ((roll.coerceIn(-45.0, 45.0) / 45.0) * 127 + 128).roundToInt().coerceIn(0, 255)
        val thr = (max(0.0, pitch - 10) / 30 * 255).roundToInt().coerceIn(0, 255)
        val brk = (max(0.0, -pitch - 10) / 30 * 255).roundToInt().coerceIn(0, 255)
        report[0] = steer.toByte(); report[1] = thr.toByte(); report[2] = brk.toByte(); report[3] = btn.toByte()
        host?.let { hid?.sendReport(it, 1, report) }
    }
    override fun onAccuracyChanged(s: Sensor?, a: Int) {}
}
