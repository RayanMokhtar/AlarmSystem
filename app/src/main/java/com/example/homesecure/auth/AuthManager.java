package com.example.homesecure.auth;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * Gestionnaire d'authentification - gère la session utilisateur locale
 * Stocke les infos dans SharedPreferences
 */
public class AuthManager {
    
    private static final String PREFS_NAME = "HomeSecureAuth";
    private static final String KEY_USER_ID = "user_id";
    private static final String KEY_EMAIL = "email";
    private static final String KEY_LOGIN = "login";
    private static final String KEY_IS_LOGGED_IN = "is_logged_in";
    private static final String KEY_ACCESS_TOKEN = "access_token";
    private static final String KEY_REFRESH_TOKEN = "refresh_token";
    
    private final SharedPreferences prefs;
    
    public AuthManager(Context context) {
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }
    
    /**
     * Sauvegarde la session utilisateur après connexion réussie
     */
    public void saveSession(DatabaseHelper.User user) {
        prefs.edit()
            .putString(KEY_USER_ID, user.id)
            .putString(KEY_EMAIL, user.email)
            .putString(KEY_LOGIN, user.login)
            .putBoolean(KEY_IS_LOGGED_IN, true)
            .apply();
    }
    
    /**
     * Sauvegarde la session utilisateur (version avec paramètres séparés)
     */
    public void saveSession(String id, String email, String login) {
        prefs.edit()
            .putString(KEY_USER_ID, id)
            .putString(KEY_EMAIL, email)
            .putString(KEY_LOGIN, login)
            .putBoolean(KEY_IS_LOGGED_IN, true)
            .apply();
    }
    
    /**
     * Sauvegarde la session avec les tokens JWT
     */
    public void saveSessionWithTokens(String id, String email, String login, String accessToken, String refreshToken) {
        prefs.edit()
            .putString(KEY_USER_ID, id)
            .putString(KEY_EMAIL, email)
            .putString(KEY_LOGIN, login)
            .putString(KEY_ACCESS_TOKEN, accessToken)
            .putString(KEY_REFRESH_TOKEN, refreshToken)
            .putBoolean(KEY_IS_LOGGED_IN, true)
            .apply();
    }
    
    /**
     * Sauvegarde uniquement le token d'accès
     */
    public void saveAccessToken(String accessToken) {
        prefs.edit()
            .putString(KEY_ACCESS_TOKEN, accessToken)
            .apply();
    }
    
    /**
     * Vérifie si l'utilisateur est connecté
     */
    public boolean isLoggedIn() {
        return prefs.getBoolean(KEY_IS_LOGGED_IN, false);
    }
    
    /**
     * Récupère le login de l'utilisateur connecté
     */
    public String getLogin() {
        return prefs.getString(KEY_LOGIN, null);
    }
    
    /**
     * Récupère l'email de l'utilisateur connecté
     */
    public String getEmail() {
        return prefs.getString(KEY_EMAIL, null);
    }
    
    /**
     * Récupère l'ID de l'utilisateur connecté
     */
    public String getUserId() {
        return prefs.getString(KEY_USER_ID, null);
    }
    
    /**
     * Récupère le token d'accès JWT
     */
    public String getAccessToken() {
        return prefs.getString(KEY_ACCESS_TOKEN, null);
    }
    
    /**
     * Récupère le token de rafraîchissement JWT
     */
    public String getRefreshToken() {
        return prefs.getString(KEY_REFRESH_TOKEN, null);
    }
    
    /**
     * Déconnecte l'utilisateur - efface la session
     */
    public void logout() {
        prefs.edit()
            .remove(KEY_USER_ID)
            .remove(KEY_EMAIL)
            .remove(KEY_LOGIN)
            .remove(KEY_ACCESS_TOKEN)
            .remove(KEY_REFRESH_TOKEN)
            .putBoolean(KEY_IS_LOGGED_IN, false)
            .apply();
    }
    
    /**
     * Efface toutes les données d'authentification
     */
    public void clearAll() {
        prefs.edit().clear().apply();
    }
}
