
package com.example.homesecure;

import android.app.Application;
import android.os.StrictMode;
import android.util.Log;

public class HomeSecureApplication extends Application {
    private static final String TAG = "HomeSecureApp";
    
    @Override
    public void onCreate() {
        super.onCreate();
        
        Log.d(TAG, "Application démarrée");
        
        // Désactiver StrictMode pour permettre les opérations réseau
        // IMPORTANT: Ceci est temporaire, pour la production il faut utiliser des requêtes asynchrones
        StrictMode.ThreadPolicy policy = new StrictMode.ThreadPolicy.Builder()
            .permitAll()
            .build();
        StrictMode.setThreadPolicy(policy);
        
        // Charger le driver PostgreSQL
        try {
            Class.forName("org.postgresql.Driver");
            Log.d(TAG, "Driver PostgreSQL chargé avec succès");
        } catch (ClassNotFoundException e) {
            Log.e(TAG, "Erreur chargement driver PostgreSQL", e);
        }
    }
}
