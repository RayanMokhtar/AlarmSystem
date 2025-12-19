package com.example.homesecure;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.example.homesecure.auth.AuthApiClient;
import com.example.homesecure.auth.AuthManager;

/**
 * Activité de connexion
 */
public class LoginActivity extends AppCompatActivity {

    private EditText etLoginOrEmail;
    private EditText etPassword;
    private Button btnLogin;
    private TextView tvRegister;
    private Button btnDevLogin;
    private ProgressBar progressBar;
    
    private AuthManager authManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);
        
        authManager = new AuthManager(this);
        
        // L'URL du serveur auth est configurée en dur dans AuthApiClient
        
        // Si déjà connecté, aller directement à MainActivity
        if (authManager.isLoggedIn()) {
            goToMain();
            return;
        }
        
        initViews();
        setupListeners();
    }
    
    private void initViews() {
        etLoginOrEmail = findViewById(R.id.etLoginOrEmail);
        etPassword = findViewById(R.id.etPassword);
        btnLogin = findViewById(R.id.btnLogin);
        tvRegister = findViewById(R.id.tvRegister);
        btnDevLogin = findViewById(R.id.btnDevLogin);
        progressBar = findViewById(R.id.progressBar);
    }
    
    private void setupListeners() {
        btnLogin.setOnClickListener(v -> attemptLogin());
        
        tvRegister.setOnClickListener(v -> {
            startActivity(new Intent(this, RegisterActivity.class));
        });
        
        // Lien vers les paramètres
        findViewById(R.id.tvSettings).setOnClickListener(v -> {
            startActivity(new Intent(this, SettingsActivity.class));
        });

        // Connexion développeur : bypass de l'authentification
        btnDevLogin.setOnClickListener(v -> devLogin());
    }
    
    private void attemptLogin() {
        String loginOrEmail = etLoginOrEmail.getText().toString().trim();
        String password = etPassword.getText().toString();
        
        // Validation
        if (loginOrEmail.isEmpty()) {
            etLoginOrEmail.setError("Entrez votre login ou email");
            etLoginOrEmail.requestFocus();
            return;
        }
        
        if (password.isEmpty()) {
            etPassword.setError("Entrez votre mot de passe");
            etPassword.requestFocus();
            return;
        }
        
        // Afficher le chargement
        setLoading(true);
        
        // Utiliser l'API HTTP au lieu de JDBC
        AuthApiClient.login(loginOrEmail, password, new AuthApiClient.AuthCallback() {
            @Override
            public void onSuccess(AuthApiClient.User user, String accessToken, String refreshToken) {
                // Au lieu de sauvegarder immédiatement, on récupère le vrai user_id
                AuthApiClient.getUserInfo(accessToken, new AuthApiClient.UserInfoCallback() {
                    @Override
                    public void onSuccess(String realUserId) {
                        setLoading(false);
                        user.id = realUserId; // On met à jour avec le vrai ID
                        
                        // Sauvegarder la session avec les tokens JWT et le VRAI ID
                        authManager.saveSessionWithTokens(user.id, user.email, user.login, accessToken, refreshToken);
                        Toast.makeText(LoginActivity.this, "Bienvenue " + user.login + " !", Toast.LENGTH_SHORT).show();
                        goToMain();
                    }

                    @Override
                    public void onError(String message) {
                        setLoading(false);
                        Toast.makeText(LoginActivity.this, "Erreur profil: " + message, Toast.LENGTH_LONG).show();
                    }
                });
            }
            
            @Override
            public void onError(String message) {
                setLoading(false);
                Toast.makeText(LoginActivity.this, message, Toast.LENGTH_LONG).show();
            }
        });
    }
    
    private void setLoading(boolean loading) {
        progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        btnLogin.setEnabled(!loading);
        etLoginOrEmail.setEnabled(!loading);
        etPassword.setEnabled(!loading);
    }

    // Bypass de connexion pour développeur
    private void devLogin() {
        // ID et credentials de développeur (non sécurisés, pour debug seulement)
        authManager.saveSession("dev", "dev@local", "dev");
        Toast.makeText(this, "Connecté en tant que développeur", Toast.LENGTH_SHORT).show();
        goToMain();
    }
    
    private void goToMain() {
        Intent intent = new Intent(this, MainActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }
}
