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
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import java.util.List;
import java.util.ArrayList;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.Call;
import okhttp3.Callback;
import java.io.IOException;
import org.json.JSONArray;
import org.json.JSONObject;

import com.example.homesecure.auth.AuthManager;
import com.example.homesecure.auth.AuthApiClient;

public class MainActivity extends AppCompatActivity {

    private static final String CHANNEL_ID = "security_alerts";
    private static final int PERMISSION_REQUEST_CODE = 101;
    
    private AuthManager authManager;
    private TextView tvWelcome;
    private TextView tvUserId;
    private Button btnLogout;
    
    private Handler notificationHandler;
    private Runnable notificationRunnable;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        // Initialize notification polling handler
        notificationHandler = new Handler(Looper.getMainLooper());
        
        // Vérifier si l'utilisateur est connecté
        authManager = new AuthManager(this);
        if (!authManager.isLoggedIn()) {
            // Rediriger vers LoginActivity
            startActivity(new Intent(this, LoginActivity.class));
            finish();
            return;
        }
        
        // Si l'ID utilisateur est temporaire ("authenticated" ou "pending"), récupérer le vrai ID
        String currentUserId = authManager.getUserId();
        if ("authenticated".equals(currentUserId) || "pending".equals(currentUserId)) {
            String accessToken = authManager.getAccessToken();
            if (accessToken != null) {
                AuthApiClient.getUserInfo(accessToken, new AuthApiClient.UserInfoCallback() {
                    @Override
                    public void onSuccess(String realUserId) {
                        // Mettre à jour la session avec le vrai ID
                        authManager.saveSessionWithTokens(realUserId, authManager.getEmail(), authManager.getLogin(), accessToken, authManager.getRefreshToken());
                        // Continuer l'initialisation
                        initializeMainActivity();
                    }
                    
                    @Override
                    public void onError(String message) {
                        Toast.makeText(MainActivity.this, "Erreur récupération ID utilisateur: " + message, Toast.LENGTH_LONG).show();
                        // Continuer avec l'ID temporaire (risque d'erreur)
                        initializeMainActivity();
                    }
                });
            } else {
                // Pas de token, rediriger vers login
                startActivity(new Intent(this, LoginActivity.class));
                finish();
                return;
            }
        } else {
            // ID valide, continuer
            initializeMainActivity();
        }
    }
    
    private void initializeMainActivity() {
        // Afficher le message de bienvenue
        setupWelcomeMessage();

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
    
    private void setupWelcomeMessage() {
        tvWelcome = findViewById(R.id.tvWelcome);
        tvUserId = findViewById(R.id.tvUserId);
        btnLogout = findViewById(R.id.btnLogout);
        
        String login = authManager.getLogin();
        if (login != null && tvWelcome != null) {
            tvWelcome.setText("Bonjour " + login);
        }
        
        // Récupérer et afficher l'ID utilisateur
        String accessToken = authManager.getAccessToken();
        if (accessToken != null && tvUserId != null) {
            tvUserId.setText("Chargement de l'ID utilisateur...");
            AuthApiClient.getUserInfo(accessToken, new AuthApiClient.UserInfoCallback() {
                @Override
                public void onSuccess(String userId) {
                    runOnUiThread(() -> tvUserId.setText("ID: " + userId));
                }
                
                @Override
                public void onError(String message) {
                    runOnUiThread(() -> tvUserId.setText("ID: Non disponible"));
                    Log.e("MainActivity", "Erreur récupération ID utilisateur: " + message);
                }
            });
        } else if (tvUserId != null) {
            tvUserId.setText("ID: Non disponible");
        }
        
        if (btnLogout != null) {
            btnLogout.setOnClickListener(v -> showLogoutConfirmation());
        }
    }
    
    private void showLogoutConfirmation() {
        new AlertDialog.Builder(this)
            .setTitle("Déconnexion")
            .setMessage("Voulez-vous vraiment vous déconnecter ?")
            .setPositiveButton("Oui", (dialog, which) -> {
                authManager.logout();
                Toast.makeText(this, "Déconnecté", Toast.LENGTH_SHORT).show();
                startActivity(new Intent(this, LoginActivity.class));
                finish();
            })
            .setNegativeButton("Non", null)
            .show();
    }

    private void setupAlertHistoryPreview() {
        RecyclerView recyclerView = findViewById(R.id.rvAlertHistoryPreview);
        recyclerView.setLayoutManager(new LinearLayoutManager(this));

        String userId = authManager.getUserId();
        if (userId != null) {
            fetchNotifications(userId, recyclerView);
        } else {
            // No user ID available, show empty list
            recyclerView.setAdapter(new AlertHistoryAdapter(new ArrayList<>()));
        }

        findViewById(R.id.layoutAlertHistoryHeader).setOnClickListener(v ->
                startActivity(new Intent(this, AlertHistoryActivity.class))
        );
        findViewById(R.id.cardAlertHistoryPreview).setOnClickListener(v ->
                startActivity(new Intent(this, AlertHistoryActivity.class))
        );
    }

    private void fetchNotifications(String userId, RecyclerView recyclerView) {
        OkHttpClient client = new OkHttpClient();
        // Utiliser l'URL de base configurée dans AuthApiClient
        String baseUrl = AuthApiClient.getBaseUrl();
        // Utiliser /auth/notifications avec filtre=false pour récupérer toutes les notifications
        String url = baseUrl + "/auth/notifications?user_id=" + userId + "&filtre=false";
        
        // Ajouter le token d'authentification si disponible
        String token = authManager.getAccessToken();
        Request.Builder requestBuilder = new Request.Builder().url(url);
        if (token != null) {
            requestBuilder.addHeader("Authorization", "Bearer " + token);
        }
        Request request = requestBuilder.build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                runOnUiThread(() -> {
                    Toast.makeText(MainActivity.this, "Erreur de chargement des notifications: " + e.getMessage(), Toast.LENGTH_SHORT).show();
                    // Show empty list on failure
                    recyclerView.setAdapter(new AlertHistoryAdapter(new ArrayList<>()));
                });
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful()) {
                    String responseBody = response.body().string();
                    try {
                        JSONObject jsonResponse = new JSONObject(responseBody);
                        if (jsonResponse.has("notifications")) {
                            JSONArray jsonArray = jsonResponse.getJSONArray("notifications");
                            List<AlertHistoryItem> notifications = new ArrayList<>();
                            for (int i = 0; i < jsonArray.length(); i++) {
                                JSONObject obj = jsonArray.getJSONObject(i);
                                String alertId = obj.getString("notification_id");
                                // Formater la date si nécessaire, ici on prend la valeur brute
                                String dateTime = obj.optString("date_notification", "Date inconnue");
                                String message = obj.optString("message", "");
                                
                                notifications.add(new AlertHistoryItem(alertId, dateTime, message));
                            }
                            
                            runOnUiThread(() -> {
                                if (notifications.isEmpty()) {
                                    Toast.makeText(MainActivity.this, "Aucune notification trouvée", Toast.LENGTH_SHORT).show();
                                }
                                // Afficher les 5 dernières ou toutes si moins de 5
                                int count = Math.min(5, notifications.size());
                                List<AlertHistoryItem> preview = notifications.subList(0, count);
                                recyclerView.setAdapter(new AlertHistoryAdapter(preview));
                            });
                        } else {
                             runOnUiThread(() -> {
                                Toast.makeText(MainActivity.this, "Format de réponse inattendu", Toast.LENGTH_SHORT).show();
                            });
                        }
                    } catch (Exception e) {
                        Log.e("MainActivity", "Erreur parsing: " + e.getMessage());
                        runOnUiThread(() -> {
                            Toast.makeText(MainActivity.this, "Erreur de traitement des données", Toast.LENGTH_SHORT).show();
                        });
                    }
                } else {
                    runOnUiThread(() -> {
                        Toast.makeText(MainActivity.this, "Erreur serveur: " + response.code(), Toast.LENGTH_SHORT).show();
                    });
                }
            }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        updateStatus();
        startNotificationPolling();
    }
    
    @Override
    protected void onPause() {
        super.onPause();
        stopNotificationPolling();
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

    private void startNotificationPolling() {
        if (notificationRunnable != null) {
            notificationHandler.removeCallbacks(notificationRunnable);
        }
        
        notificationRunnable = new Runnable() {
            @Override
            public void run() {
                pollForNotifications();
                // Schedule next poll in 10 seconds
                notificationHandler.postDelayed(this, 10000);
            }
        };
        
        // Start polling immediately
        notificationHandler.post(notificationRunnable);
    }
    
    private void stopNotificationPolling() {
        if (notificationRunnable != null) {
            notificationHandler.removeCallbacks(notificationRunnable);
            notificationRunnable = null;
        }
    }
    
    private void pollForNotifications() {
        String userId = authManager.getUserId();
        if (userId == null || "authenticated".equals(userId) || "pending".equals(userId)) {
            return; // Skip if no valid user ID
        }
        
        OkHttpClient client = new OkHttpClient();
        String baseUrl = AuthApiClient.getBaseUrl();
        // Use service_calcul route for polling unread notifications
        String url = baseUrl + "/auth/notifsnonlues?utilisateur_id=" + userId;
        
        String token = authManager.getAccessToken();
        Request.Builder requestBuilder = new Request.Builder().url(url);
        if (token != null) {
            requestBuilder.addHeader("Authorization", "Bearer " + token);
        }
        Request request = requestBuilder.build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                Log.d("NotificationPolling", "Failed to poll notifications: " + e.getMessage());
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful()) {
                    String responseBody = response.body().string();
                    try {
                        // Service_calcul returns {"status":"success","notifications":[...]}
                        JSONObject jsonResponse = new JSONObject(responseBody);
                        if (jsonResponse.has("notifications")) {
                            JSONArray jsonArray = jsonResponse.getJSONArray("notifications");
                            if (jsonArray.length() > 0) {
                                // There are unread notifications, trigger alert
                                runOnUiThread(() -> triggerSecurityNotification());
                            }
                        }
                    } catch (Exception e) {
                        Log.e("NotificationPolling", "Error parsing response: " + e.getMessage());
                    }
                }
            }
        });
    }
    
    private void triggerSecurityNotification() {
        // Check for Android 13+ Notification Permission
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                return; // Skip if no permission
            }
        }

        // Create an explicit intent for CameraActivity
        Intent intent = new Intent(this, CameraActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        intent.putExtra("EXTRA_ALERT", true);

        PendingIntent pendingIntent = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE);

        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_dialog_alert)
                .setContentTitle("Alerte Sécurité!")
                .setContentText("Nouvelle notification de sécurité détectée.")
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setContentIntent(pendingIntent)
                .setAutoCancel(true);

        try {
            NotificationManagerCompat notificationManager = NotificationManagerCompat.from(this);
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED) {
                notificationManager.notify(1002, builder.build());
            }
        } catch (SecurityException e) {
            Log.e("NotificationPolling", "Permission missing for notifications");
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