package com.markyhzhang.poppyandroid;

import android.support.design.widget.Snackbar;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.WebSocket;

public class MainActivity extends AppCompatActivity {

    private OkHttpClient client;
    private Request request = new Request.Builder().url("ws://40.117.127.142:9001/socket").build();
    private ConnectionListener connection;
    private WebSocket ws;
    private TextView tv;
    private Snackbar snackbar;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        tv = findViewById(R.id.text_status);
        client = new OkHttpClient();
        snackbar = Snackbar.make(findViewById(R.id.main_layout), "",
                Snackbar.LENGTH_SHORT);
        connection = new ConnectionListener(tv, snackbar);
    }

    public void performAction(View view){
        String t = ((TextView)view).getText().toString();
        System.out.println(t);
        if (t.equals(getResources().getString(R.string.connect))) {
            ws = client.newWebSocket(request, connection);
            System.out.println("Connecting to Poppy...");
            tv.setText("Status: Connecting...");
        } else if (t.equals(getResources().getString(R.string.disconnect))) {
            ws.close(1000, "bye");
            tv.setText("Status: Disconnected");
        }
        if (connection.isConnected()) {
            // Basic movement commands
            if (t.equals(getResources().getString(R.string.forward))) {
                connection.moveForwards();
            } else if (t.equals(getResources().getString(R.string.backward))) {
                connection.moveBackwards();
            } else if (t.equals(getResources().getString(R.string.left))) {
                connection.turn(10);
            } else if (t.equals(getResources().getString(R.string.right))) {
                connection.turn(-10);
            }
            // Enhanced commands
            else if (t.equals("Find Face")) {
                connection.sendCommand("find_face");
            } else if (t.equals("Dance")) {
                connection.sendCommand("dance");
            } else if (t.equals("Stop")) {
                connection.sendCommand("stop");
            } else if (t.equals("Calibrate")) {
                connection.sendCommand("calibrate");
            } else if (t.equals("Dock")) {
                connection.sendCommand("docking_start");
            } else if (t.equals("Undock")) {
                connection.sendCommand("docking_stop");
            } else if (t.equals("Emergency Stop")) {
                connection.sendCommand("emergency_stop");
            } else if (t.equals("Battery Status")) {
                connection.sendCommand("battery_status");
            } else if (t.equals("System Status")) {
                connection.sendCommand("system_status");
            } else if (t.equals("IMU Calibration")) {
                connection.sendCommand("imu_calibrate");
            } else if (t.equals("Spatial Calibration")) {
                connection.sendCommand("spatial_calibrate");
            } else if (t.equals("Docking Calibration")) {
                connection.sendCommand("docking_calibrate");
            } else if (t.equals("Motor Test")) {
                connection.sendCommand("motor_test");
            } else if (t.equals("Spatial Awareness On")) {
                connection.sendCommand("spatial_awareness_on");
            } else if (t.equals("Spatial Awareness Off")) {
                connection.sendCommand("spatial_awareness_off");
            } else if (t.equals("Adaptive PID On")) {
                connection.sendCommand("adaptive_pid_on");
            } else if (t.equals("Adaptive PID Off")) {
                connection.sendCommand("adaptive_pid_off");
            } else if (t.equals("Voice Control On")) {
                connection.sendCommand("voice_control_on");
            } else if (t.equals("Voice Control Off")) {
                connection.sendCommand("voice_control_off");
            }
        }else{
            showSnackbar("Not connected to server!");
        }
    }

    public void showSnackbar(String msg){
        snackbar.setText(msg).show();
    }
}
