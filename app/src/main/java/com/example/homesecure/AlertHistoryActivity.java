package com.example.homesecure;

import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.example.homesecure.auth.AuthApiClient;
import com.example.homesecure.auth.AuthManager;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

public class AlertHistoryActivity extends AppCompatActivity {

    private AuthManager authManager;
    private RecyclerView recyclerView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_alert_history);

        authManager = new AuthManager(this);

        View btnBack = findViewById(R.id.btnBack);
        btnBack.setOnClickListener(v -> finish());

        recyclerView = findViewById(R.id.rvAlertHistoryFull);
        recyclerView.setLayoutManager(new LinearLayoutManager(this));

        // Charger les notifications réelles
        String userId = authManager.getUserId();
        if (userId != null && !userId.equals("authenticated") && !userId.equals("pending")) {
            fetchNotifications(userId, recyclerView);
        } else {
            Toast.makeText(this, "Utilisateur non identifié", Toast.LENGTH_SHORT).show();
            finish();
        }
    }

    private void fetchNotifications(String userId, RecyclerView recyclerView) {
        OkHttpClient client = new OkHttpClient();
        String baseUrl = AuthApiClient.getBaseUrl();
        String url = baseUrl + "/auth/notifications?user_id=" + userId + "&filtre=false";
        
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
                    Toast.makeText(AlertHistoryActivity.this, "Erreur de chargement des notifications: " + e.getMessage(), Toast.LENGTH_SHORT).show();
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
                                String dateTime = obj.optString("date_notification", "Date inconnue");
                                String message = obj.optString("message", "");
                                
                                notifications.add(new AlertHistoryItem(alertId, dateTime, message));
                            }
                            
                            runOnUiThread(() -> {
                                if (notifications.isEmpty()) {
                                    Toast.makeText(AlertHistoryActivity.this, "Aucune notification trouvée", Toast.LENGTH_SHORT).show();
                                }
                                recyclerView.setAdapter(new AlertHistoryAdapter(notifications));
                            });
                        } else {
                            runOnUiThread(() -> {
                                Toast.makeText(AlertHistoryActivity.this, "Format de réponse inattendu", Toast.LENGTH_SHORT).show();
                            });
                        }
                    } catch (Exception e) {
                        Log.e("AlertHistoryActivity", "Erreur parsing: " + e.getMessage());
                        runOnUiThread(() -> {
                            Toast.makeText(AlertHistoryActivity.this, "Erreur de traitement des données", Toast.LENGTH_SHORT).show();
                        });
                    }
                } else {
                    runOnUiThread(() -> {
                        Toast.makeText(AlertHistoryActivity.this, "Erreur serveur: " + response.code(), Toast.LENGTH_SHORT).show();
                    });
                }
            }
        });
    }
}
