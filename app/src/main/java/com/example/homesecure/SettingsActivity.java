package com.example.homesecure;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.RadioGroup;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

public class SettingsActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings);

        EditText etIp = findViewById(R.id.etIpAddress);
        EditText etPort = findViewById(R.id.etPort);
        EditText etPass = findViewById(R.id.etPassword);
        Button btnSave = findViewById(R.id.btnSaveSettings);
        RadioGroup rgSecurity = findViewById(R.id.rgSecurityLevel);

        // Load existing settings
        SharedPreferences sharedPref = getSharedPreferences("HomeSecurePrefs", Context.MODE_PRIVATE);
        String savedIp = sharedPref.getString("RP_IP", "");
        String savedPort = sharedPref.getString("RP_PORT", "");

        // Backward compatibility: if user previously stored "IP:PORT" in RP_IP
        if (savedPort.isEmpty() && savedIp != null && savedIp.contains(":")) {
            String[] parts = savedIp.split(":", 2);
            savedIp = parts[0];
            savedPort = parts.length > 1 ? parts[1] : "";
        }

        etIp.setText(savedIp);
        etPort.setText(savedPort);
        etPass.setText(sharedPref.getString("RP_PASS", ""));

        // Load Security Level
        int savedLevel = sharedPref.getInt("SECURITY_LEVEL", R.id.rbNormal);
        rgSecurity.check(savedLevel);

        btnSave.setOnClickListener(v -> {
            String ip = etIp.getText().toString();
            String port = etPort.getText().toString();
            String pass = etPass.getText().toString();
            int selectedLevel = rgSecurity.getCheckedRadioButtonId();

            if (ip.isEmpty() || pass.isEmpty()) {
                Toast.makeText(this, "Please fill all fields", Toast.LENGTH_SHORT).show();
                return;
            }

            SharedPreferences.Editor editor = sharedPref.edit();
            editor.putString("RP_IP", ip);
            editor.putString("RP_PORT", port);
            editor.putString("RP_PASS", pass);
            editor.putInt("SECURITY_LEVEL", selectedLevel);
            editor.apply();

            Toast.makeText(this, "Configuration Saved", Toast.LENGTH_SHORT).show();
            finish(); // Go back to main
        });
    }
}