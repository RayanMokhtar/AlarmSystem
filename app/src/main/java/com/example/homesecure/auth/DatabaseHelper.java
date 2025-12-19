package com.example.homesecure.auth;

import android.os.StrictMode;
import android.util.Log;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Timestamp;
import java.util.UUID;

/**
 * Helper pour les opérations de base de données
 * NOTE: Connexion directe - à remplacer par API REST + JWT en production
 */
public class DatabaseHelper {
    
    private static final String TAG = "DatabaseHelper";
    
    static {
        // Permet les opérations réseau sur le thread principal (temporaire pour dev)
        StrictMode.ThreadPolicy policy = new StrictMode.ThreadPolicy.Builder().permitAll().build();
        StrictMode.setThreadPolicy(policy);
    }
    
    /**
     * Obtient une connexion à la base de données
     */
    private static Connection getConnection() throws Exception {
        Log.d(TAG, "Tentative de connexion à: " + DatabaseConfig.getConnectionUrl());
        try {
            Class.forName("org.postgresql.Driver");
            Connection conn = DriverManager.getConnection(
                DatabaseConfig.getConnectionUrl(),
                DatabaseConfig.DB_USER,
                DatabaseConfig.DB_PASSWORD
            );
            Log.d(TAG, "Connexion réussie !");
            return conn;
        } catch (Exception e) {
            Log.e(TAG, "Erreur connexion DB: " + e.getClass().getSimpleName() + " - " + e.getMessage());
            throw e;
        }
    }
    
    /**
     * Vérifie les identifiants de connexion
     * @param loginOrEmail Login ou email de l'utilisateur
     * @param password Mot de passe en clair
     * @return User si authentifié, null sinon
     */
    public static User login(String loginOrEmail, String password) {
        Log.d(TAG, "Tentative de login pour: " + loginOrEmail);
        Connection conn = null;
        try {
            conn = getConnection();
            String sql = "SELECT utilisateur_id, email, login FROM utilisateur " +
                        "WHERE (login = ? OR email = ?) AND motdepasse = ?";
            
            PreparedStatement stmt = conn.prepareStatement(sql);
            stmt.setString(1, loginOrEmail);
            stmt.setString(2, loginOrEmail);
            stmt.setString(3, password);
            
            Log.d(TAG, "Exécution de la requête login...");
            ResultSet rs = stmt.executeQuery();
            
            if (rs.next()) {
                User user = new User();
                user.id = rs.getString("utilisateur_id");
                user.email = rs.getString("email");
                user.login = rs.getString("login");
                Log.d(TAG, "Login réussi pour: " + user.login);
                return user;
            } else {
                Log.d(TAG, "Aucun utilisateur trouvé avec ces identifiants");
            }
            
        } catch (Exception e) {
            Log.e(TAG, "Erreur login: " + e.getMessage(), e);
            e.printStackTrace();
        } finally {
            try {
                if (conn != null) conn.close();
            } catch (Exception e) {
                Log.e(TAG, "Erreur fermeture connexion: " + e.getMessage());
            }
        }
        
        return null;
    }
    
    /**
     * Inscrit un nouvel utilisateur
     * @param email Email unique
     * @param login Login unique
     * @param password Mot de passe
     * @return true si inscription réussie
     */
    public static RegisterResult register(String email, String login, String password) {
        Log.d(TAG, "Tentative d'inscription pour: " + login + " / " + email);
        Connection conn = null;
        try {
            conn = getConnection();
            
            // Vérifier si email existe déjà
            String checkEmail = "SELECT 1 FROM utilisateur WHERE email = ?";
            PreparedStatement checkStmt = conn.prepareStatement(checkEmail);
            checkStmt.setString(1, email);
            ResultSet rsEmail = checkStmt.executeQuery();
            if (rsEmail.next()) {
                Log.d(TAG, "Email déjà utilisé: " + email);
                return new RegisterResult(false, "Cet email est déjà utilisé");
            }
            
            // Vérifier si login existe déjà
            String checkLogin = "SELECT 1 FROM utilisateur WHERE login = ?";
            checkStmt = conn.prepareStatement(checkLogin);
            checkStmt.setString(1, login);
            ResultSet rsLogin = checkStmt.executeQuery();
            if (rsLogin.next()) {
                Log.d(TAG, "Login déjà pris: " + login);
                return new RegisterResult(false, "Ce login est déjà pris");
            }
            
            // Insérer le nouvel utilisateur
            String sql = "INSERT INTO utilisateur (utilisateur_id, email, motdepasse, date_creation, login) " +
                        "VALUES (?, ?, ?, ?, ?)";
            
            PreparedStatement stmt = conn.prepareStatement(sql);
            UUID userId = UUID.randomUUID();
            stmt.setObject(1, userId);
            stmt.setString(2, email);
            stmt.setString(3, password);
            stmt.setTimestamp(4, new Timestamp(System.currentTimeMillis()));
            stmt.setString(5, login);
            
            Log.d(TAG, "Insertion de l'utilisateur...");
            int rows = stmt.executeUpdate();
            
            if (rows > 0) {
                Log.d(TAG, "Inscription réussie ! Utilisateur ID: " + userId);
                return new RegisterResult(true, "Inscription réussie");
            } else {
                Log.e(TAG, "Aucune ligne insérée");
                return new RegisterResult(false, "Erreur lors de l'inscription");
            }
            
        } catch (Exception e) {
            Log.e(TAG, "Erreur register: " + e.getMessage(), e);
            e.printStackTrace();
            return new RegisterResult(false, "Erreur: " + e.getMessage());
        } finally {
            try {
                if (conn != null) conn.close();
            } catch (Exception e) {
                Log.e(TAG, "Erreur fermeture connexion: " + e.getMessage());
            }
        }
    }
    
    /**
     * Teste la connexion à la base de données
     */
    public static boolean testConnection() {
        Log.d(TAG, "Test de connexion à la base...");
        Connection conn = null;
        try {
            conn = getConnection();
            boolean isValid = conn != null && !conn.isClosed();
            Log.d(TAG, "Test connexion: " + (isValid ? "OK" : "FAILED"));
            return isValid;
        } catch (Exception e) {
            Log.e(TAG, "Test connexion échoué: " + e.getMessage(), e);
            return false;
        } finally {
            try {
                if (conn != null) conn.close();
            } catch (Exception e) {
                Log.e(TAG, "Erreur fermeture connexion: " + e.getMessage());
            }
        }
    }
    
    // Classes internes
    
    public static class User {
        public String id;
        public String email;
        public String login;
    }
    
    public static class RegisterResult {
        public boolean success;
        public String message;
        
        public RegisterResult(boolean success, String message) {
            this.success = success;
            this.message = message;
        }
    }
}
