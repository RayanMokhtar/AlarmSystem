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

    // Constantes pour les modes de streaming
    public static final String PREF_STREAMING_MODE = "STREAMING_MODE";
    public static final String MODE_AUTO = "auto";
    public static final String MODE_WEBRTC = "webrtc";
    public static final String MODE_MJPEG = "mjpeg";
    
    // Constantes pour le serveur caméra
    public static final String PREF_CAMERA_IP = "CAMERA_IP";
    public static final String PREF_CAMERA_PORT = "CAMERA_PORT";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings);

        // Champs serveur caméra
        EditText etIp = findViewById(R.id.etIpAddress);
        EditText etPort = findViewById(R.id.etPort);
        
        // Autres champs
        EditText etPass = findViewById(R.id.etPassword);
        Button btnSave = findViewById(R.id.btnSaveSettings);
        RadioGroup rgSecurity = findViewById(R.id.rgSecurityLevel);
        RadioGroup rgStreamingMode = findViewById(R.id.rgStreamingMode);

        // Load existing settings
        SharedPreferences sharedPref = getSharedPreferences("HomeSecurePrefs", Context.MODE_PRIVATE);
        
        // Serveur caméra
        String savedCameraIp = sharedPref.getString(PREF_CAMERA_IP, "");
        String savedCameraPort = sharedPref.getString(PREF_CAMERA_PORT, "8090");
        
        // Backward compatibility avec ancien format
        if (savedCameraIp.isEmpty()) {
            savedCameraIp = sharedPref.getString("RP_IP", "");
            if (savedCameraIp.contains(":")) {
                String[] parts = savedCameraIp.split(":", 2);
                savedCameraIp = parts[0];
                savedCameraPort = parts.length > 1 ? parts[1] : "8090";
            }
        }

        etIp.setText(savedCameraIp);
        etPort.setText(savedCameraPort);
        etPass.setText(sharedPref.getString("RP_PASS", ""));

        // Load Security Level
        int savedLevel = sharedPref.getInt("SECURITY_LEVEL", R.id.rbNormal);
        rgSecurity.check(savedLevel);

        // Load Streaming Mode (MJPEG par défaut car plus compatible)
        String savedMode = sharedPref.getString(PREF_STREAMING_MODE, MODE_MJPEG);
        switch (savedMode) {
            case MODE_WEBRTC:
                rgStreamingMode.check(R.id.rbModeWebRTC);
                break;
            case MODE_MJPEG:
                rgStreamingMode.check(R.id.rbModeMJPEG);
                break;
            default:
                rgStreamingMode.check(R.id.rbModeAuto);
                break;
        }

        btnSave.setOnClickListener(v -> {
            String cameraIp = etIp.getText().toString().trim();
            String cameraPort = etPort.getText().toString().trim();
            String pass = etPass.getText().toString();
            int selectedLevel = rgSecurity.getCheckedRadioButtonId();
            int selectedMode = rgStreamingMode.getCheckedRadioButtonId();

            // Convertir le mode sélectionné en string
            String streamingMode;
            if (selectedMode == R.id.rbModeWebRTC) {
                streamingMode = MODE_WEBRTC;
            } else if (selectedMode == R.id.rbModeMJPEG) {
                streamingMode = MODE_MJPEG;
            } else {
                streamingMode = MODE_AUTO;
            }

            // Validation
            if (cameraIp.isEmpty()) {
                Toast.makeText(this, "Entrez l'adresse du serveur caméra", Toast.LENGTH_SHORT).show();
                return;
            }

            // Port par défaut
            if (cameraPort.isEmpty()) cameraPort = "8090";

            SharedPreferences.Editor editor = sharedPref.edit();
            // Serveur caméra
            editor.putString(PREF_CAMERA_IP, cameraIp);
            editor.putString(PREF_CAMERA_PORT, cameraPort);
            // Anciens champs pour compatibilité
            editor.putString("RP_IP", cameraIp);
            editor.putString("RP_PORT", cameraPort);
            editor.putString("RP_PASS", pass);
            // Autres
            editor.putInt("SECURITY_LEVEL", selectedLevel);
            editor.putString(PREF_STREAMING_MODE, streamingMode);
            editor.apply();

            Toast.makeText(this, "Configuration sauvegardée", Toast.LENGTH_SHORT).show();
            finish();
        });
    }
}