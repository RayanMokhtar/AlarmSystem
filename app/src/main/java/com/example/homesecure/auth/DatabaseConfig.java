package com.example.homesecure.auth;

/**
 * Configuration de la base de données PostgreSQL
 * À REMPLIR avec vos identifiants
 */
public class DatabaseConfig {
    
    // ============================================
    // REMPLIR CES VALEURS AVEC VOS IDENTIFIANTS
    // ============================================
    
    public static final String DB_HOST = "postgresql-hammal.alwaysdata.net";          // Ex: "localhost", "192.168.1.10", "db.exemple.com"
    public static final String DB_PORT = "5432";                 // Port PostgreSQL par défaut
    public static final String DB_NAME = "hammal_aterlierrt";    // Nom de la base
    public static final String DB_USER = "hammal";    // Utilisateur PostgreSQL
    public static final String DB_PASSWORD = "Zahrdin.99"; // Mot de passe
    
    // ============================================
    
    /**
     * Génère l'URL de connexion JDBC
     */
    public static String getConnectionUrl() {
        return "jdbc:postgresql://" + DB_HOST + ":" + DB_PORT + "/" + DB_NAME;
    }
}
