package com.example.homesecure.auth;

import android.os.Handler;
import android.os.Looper;
import android.util.Log;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Client HTTP pour l'API d'authentification
 * Remplace la connexion JDBC directe qui ne fonctionne pas sur Android
 */
public class AuthApiClient {
    
    private static final String TAG = "AuthApiClient";
    
    // URL du serveur d'orchestration (service_calcul)
    // 10.0.2.2 est l'adresse spéciale pour accéder au localhost de la machine hôte depuis l'émulateur Android
    private static String BASE_URL = "http://10.12.241.207:8080/api/serveur_calcul";
    
    private static final ExecutorService executor = Executors.newSingleThreadExecutor();
    private static final Handler mainHandler = new Handler(Looper.getMainLooper());
    
    /**
     * Configure l'URL de base du serveur d'authentification
     */
    public static void setBaseUrl(String url) {
        BASE_URL = url;
        Log.d(TAG, "Base URL configurée: " + BASE_URL);
    }
    
    public static String getBaseUrl() {
        return BASE_URL;
    }
    
    /**
     * Callback pour les opérations async
     */
    public interface AuthCallback {
        void onSuccess(User user, String accessToken, String refreshToken);
        void onError(String message);
    }
    
    public interface RegisterCallback {
        void onSuccess(String message);
        void onError(String message);
    }
    
    public interface ConnectionCallback {
        void onResult(boolean connected, String message);
    }
    
    /**
     * Teste la connexion au serveur d'authentification
     */
    public static void testConnection(ConnectionCallback callback) {
        executor.execute(() -> {
            try {
                Log.d(TAG, "Test connexion à: " + BASE_URL + "/health");
                
                URL url = new URL(BASE_URL + "/health");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                conn.setConnectTimeout(5000);
                conn.setReadTimeout(5000);
                
                int responseCode = conn.getResponseCode();
                
                if (responseCode == 200) {
                    BufferedReader reader = new BufferedReader(
                        new InputStreamReader(conn.getInputStream())
                    );
                    StringBuilder response = new StringBuilder();
                    String line;
                    while ((line = reader.readLine()) != null) {
                        response.append(line);
                    }
                    reader.close();
                    
                    JSONObject json = new JSONObject(response.toString());
                    String status = json.optString("status", "unknown");
                    
                    boolean connected = "healthy".equals(status);
                    Log.d(TAG, "Test connexion: " + (connected ? "OK" : "FAILED"));
                    
                    mainHandler.post(() -> callback.onResult(connected, 
                        connected ? "Serveur connecté" : "Serveur non disponible"));
                } else {
                    Log.e(TAG, "Test connexion échoué: HTTP " + responseCode);
                    mainHandler.post(() -> callback.onResult(false, "HTTP " + responseCode));
                }
                
                conn.disconnect();
                
            } catch (Exception e) {
                Log.e(TAG, "Erreur test connexion: " + e.getMessage(), e);
                mainHandler.post(() -> callback.onResult(false, e.getMessage()));
            }
        });
    }
    
    /**
     * Authentifie un utilisateur
     */
    public static void login(String loginOrEmail, String password, AuthCallback callback) {
        executor.execute(() -> {
            try {
                Log.d(TAG, "Tentative de login pour: " + loginOrEmail);
                
                URL url = new URL(BASE_URL + "/auth/connexion");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                conn.setConnectTimeout(10000);
                conn.setReadTimeout(10000);
                
                // Corps de la requête (adapté pour service_calcul)
                JSONObject body = new JSONObject();
                body.put("email", loginOrEmail);
                body.put("motdepasse", password);
                
                Log.d(TAG, "Envoi requête login à service_calcul...");
                
                OutputStream os = conn.getOutputStream();
                os.write(body.toString().getBytes(StandardCharsets.UTF_8));
                os.close();
                
                int responseCode = conn.getResponseCode();
                Log.d(TAG, "Réponse HTTP: " + responseCode);
                
                BufferedReader reader;
                if (responseCode >= 200 && responseCode < 300) {
                    reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                } else {
                    reader = new BufferedReader(new InputStreamReader(conn.getErrorStream()));
                }
                
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    response.append(line);
                }
                reader.close();
                conn.disconnect();
                
                Log.d(TAG, "Réponse: " + response);
                
                JSONObject json = new JSONObject(response.toString());
                String accessToken = json.optString("access_token", null);
                String refreshToken = json.optString("refresh_token", null);
                
                if (accessToken != null) {
                    // Login réussi - On crée un objet User minimal
                    // L'ID réel sera récupéré via getUserInfo dans LoginActivity
                    User user = new User();
                    user.id = json.optString("user_id", "pending"); 
                    user.email = loginOrEmail;
                    user.login = loginOrEmail.contains("@") ? loginOrEmail.split("@")[0] : loginOrEmail;
                    
                    Log.d(TAG, "Login réussi via service_calcul, token reçu");
                    final String finalAccessToken = accessToken;
                    final String finalRefreshToken = refreshToken;
                    mainHandler.post(() -> callback.onSuccess(user, finalAccessToken, finalRefreshToken));
                } else {
                    String message = json.optString("detail", "Email ou mot de passe incorrect");
                    Log.d(TAG, "Login échoué: " + message);
                    mainHandler.post(() -> callback.onError(message));
                }
                
            } catch (Exception e) {
                Log.e(TAG, "Erreur login: " + e.getMessage(), e);
                mainHandler.post(() -> callback.onError("Erreur réseau: " + e.getMessage()));
            }
        });
    }
    
    /**
     * Inscrit un nouvel utilisateur
     */
    public static void register(String email, String login, String password, RegisterCallback callback) {
        register(email, login, password, "Adresse non spécifiée", callback);
    }

    /**
     * Inscrit un nouvel utilisateur avec adresse
     */
    public static void register(String email, String login, String password, String address, RegisterCallback callback) {
        executor.execute(() -> {
            try {
                Log.d(TAG, "Tentative d'inscription: " + login + " / " + email);
                
                // service_calcul attend des paramètres de requête pour /auth/inscrire
                String query = String.format("email=%s&motdepasse=%s&login=%s&adresse=%s",
                        java.net.URLEncoder.encode(email, "UTF-8"),
                        java.net.URLEncoder.encode(password, "UTF-8"),
                        java.net.URLEncoder.encode(login, "UTF-8"),
                        java.net.URLEncoder.encode(address, "UTF-8"));
                
                URL url = new URL(BASE_URL + "/auth/inscrire?" + query);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                conn.setConnectTimeout(10000);
                conn.setReadTimeout(10000);
                
                Log.d(TAG, "Envoi requête register à: " + url.toString());
                
                // Pas de corps nécessaire car tout est dans l'URL (FastAPI query params)
                OutputStream os = conn.getOutputStream();
                os.write("{}".getBytes(StandardCharsets.UTF_8));
                os.close();
                
                int responseCode = conn.getResponseCode();
                Log.d(TAG, "Réponse HTTP: " + responseCode);
                
                BufferedReader reader;
                if (responseCode >= 200 && responseCode < 300) {
                    reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                } else {
                    reader = new BufferedReader(new InputStreamReader(conn.getErrorStream()));
                }
                
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    response.append(line);
                }
                reader.close();
                conn.disconnect();
                
                Log.d(TAG, "Réponse: " + response);
                
                JSONObject json = new JSONObject(response.toString());
                String status = json.optString("status", "");
                
                if ("success".equals(status)) {
                    Log.d(TAG, "Inscription réussie !");
                    mainHandler.post(() -> callback.onSuccess("Inscription réussie"));
                } else {
                    String detail = json.optString("detail", "Erreur lors de l'inscription");
                    Log.d(TAG, "Inscription échouée: " + detail);
                    mainHandler.post(() -> callback.onError(detail));
                }
                
            } catch (Exception e) {
                Log.e(TAG, "Erreur register: " + e.getMessage(), e);
                mainHandler.post(() -> callback.onError("Erreur réseau: " + e.getMessage()));
            }
        });
    }
    
    public interface UserInfoCallback {
        void onSuccess(String userId);
        void onError(String message);
    }
    
    /**
     * Récupère les informations de l'utilisateur connecté
     */
    public static void getUserInfo(String accessToken, UserInfoCallback callback) {
        executor.execute(() -> {
            try {
                Log.d(TAG, "Récupération des infos utilisateur");
                
                URL url = new URL(BASE_URL + "/auth/me");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                conn.setRequestProperty("accept", "application/json");
                addAuthHeader(conn, accessToken);
                conn.setConnectTimeout(10000);
                conn.setReadTimeout(10000);
                
                int responseCode = conn.getResponseCode();
                Log.d(TAG, "Réponse HTTP: " + responseCode);
                
                BufferedReader reader;
                if (responseCode >= 200 && responseCode < 300) {
                    reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                } else {
                    reader = new BufferedReader(new InputStreamReader(conn.getErrorStream()));
                }
                
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    response.append(line);
                }
                reader.close();
                conn.disconnect();
                
                Log.d(TAG, "Réponse: " + response);
                
                JSONObject json = new JSONObject(response.toString());
                String userId = json.optString("user_id", null);
                
                if (userId != null) {
                    Log.d(TAG, "ID utilisateur récupéré: " + userId);
                    mainHandler.post(() -> callback.onSuccess(userId));
                } else {
                    String message = json.optString("detail", "Erreur lors de la récupération des infos utilisateur");
                    Log.d(TAG, "Échec récupération ID: " + message);
                    mainHandler.post(() -> callback.onError(message));
                }
                
            } catch (Exception e) {
                Log.e(TAG, "Erreur getUserInfo: " + e.getMessage(), e);
                mainHandler.post(() -> callback.onError("Erreur réseau: " + e.getMessage()));
            }
        });
    }
    
    /**
     * Ajoute le header d'authentification à une connexion HTTP
     */
    public static void addAuthHeader(HttpURLConnection conn, String accessToken) {
        if (accessToken != null && !accessToken.isEmpty()) {
            conn.setRequestProperty("Authorization", "Bearer " + accessToken);
            Log.d(TAG, "Token JWT ajouté à la requête");
        }
    }
    
    /**
     * Représente un utilisateur authentifié
     */
    public static class User {
        public String id;
        public String email;
        public String login;
    }
}
