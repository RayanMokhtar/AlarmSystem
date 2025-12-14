package com.example.homesecure;

import android.Manifest;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import java.util.List;

public class MainActivity extends AppCompatActivity {

    private static final String CHANNEL_ID = "security_alerts";
    private static final int PERMISSION_REQUEST_CODE = 101;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        createNotificationChannel();

        setupAlertHistoryPreview();

        findViewById(R.id.btnSettings).setOnClickListener(v -> 
            startActivity(new Intent(this, SettingsActivity.class))
        );

        findViewById(R.id.btnViewCamera).setOnClickListener(v -> 
            startActivity(new Intent(this, CameraActivity.class))
        );

        findViewById(R.id.btnSimulateAlert).setOnClickListener(v -> 
            triggerMockNotification()
        );
    }

    private void setupAlertHistoryPreview() {
        RecyclerView recyclerView = findViewById(R.id.rvAlertHistoryPreview);
        recyclerView.setLayoutManager(new LinearLayoutManager(this));

        List<AlertHistoryItem> all = AlertHistoryRepository.getFakeHistory();
        int count = Math.min(3, all.size());
        List<AlertHistoryItem> preview = all.subList(0, count);
        recyclerView.setAdapter(new AlertHistoryAdapter(preview));

        findViewById(R.id.layoutAlertHistoryHeader).setOnClickListener(v ->
                startActivity(new Intent(this, AlertHistoryActivity.class))
        );
        findViewById(R.id.cardAlertHistoryPreview).setOnClickListener(v ->
                startActivity(new Intent(this, AlertHistoryActivity.class))
        );
    }

    @Override
    protected void onResume() {
        super.onResume();
        updateStatus();
    }

    private void updateStatus() {
        SharedPreferences sharedPref = getSharedPreferences("HomeSecurePrefs", Context.MODE_PRIVATE);
        String ip = sharedPref.getString("RP_IP", null);
        String port = sharedPref.getString("RP_PORT", "");
        int securityLevelId = sharedPref.getInt("SECURITY_LEVEL", R.id.rbNormal);

        TextView tvStatus = findViewById(R.id.tvSystemStatus);
        TextView tvInfo = findViewById(R.id.tvConfigInfo);

        if (ip == null || ip.isEmpty()) {
            tvStatus.setText("Configuration Required");
            tvInfo.setText("Please set IP in Settings");
        } else {
            // Display Security Level
            String levelText;
            if (securityLevelId == R.id.rbDisabled) {
                levelText = "System Disabled";
            } else if (securityLevelId == R.id.rbContinuous) {
                levelText = "Continuous Monitoring";
            } else {
                levelText = "System Armed (Normal)";
            }

            tvStatus.setText(levelText);
            String finalPort = (port == null || port.isEmpty()) ? "8080" : port;
            tvInfo.setText("Connected to: " + ip + ":" + finalPort);
        }
    }

    private void triggerMockNotification() {
        // Check for Android 13+ Notification Permission
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.POST_NOTIFICATIONS}, PERMISSION_REQUEST_CODE);
                return;
            }
        }

        // Create an explicit intent for an Activity in your app
        Intent intent = new Intent(this, CameraActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        intent.putExtra("EXTRA_ALERT", true); // Signal that this is an alert

        PendingIntent pendingIntent = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE);

        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_dialog_alert)
                .setContentTitle("Security Alert!")
                .setContentText("Motion detected in the main hall.")
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setContentIntent(pendingIntent)
                .setAutoCancel(true);

        try {
            NotificationManagerCompat notificationManager = NotificationManagerCompat.from(this);
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED) {
                notificationManager.notify(1001, builder.build());
                Toast.makeText(this, "Notification Sent! Check Status Bar.", Toast.LENGTH_LONG).show();
            }
        } catch (SecurityException e) {
            Toast.makeText(this, "Permission missing for notifications", Toast.LENGTH_SHORT).show();
        }
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            CharSequence name = "Security Alerts";
            String description = "High priority security notifications";
            int importance = NotificationManager.IMPORTANCE_HIGH;
            NotificationChannel channel = new NotificationChannel(CHANNEL_ID, name, importance);
            channel.setDescription(description);
            
            NotificationManager notificationManager = getSystemService(NotificationManager.class);
            if (notificationManager != null) {
                notificationManager.createNotificationChannel(channel);
            }
        }
    }
}