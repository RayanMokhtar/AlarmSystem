package com.example.homesecure;

import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.example.homesecure.auth.AuthApiClient;

/**
 * Activité d'inscription
 */
public class RegisterActivity extends AppCompatActivity {

    private EditText etEmail;
    private EditText etLogin;
    private EditText etPassword;
    private EditText etPasswordConfirm;
    private Button btnRegister;
    private TextView tvLogin;
    private ProgressBar progressBar;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_register);
        
        // L'URL du serveur auth est configurée en dur dans AuthApiClient
        
        initViews();
        setupListeners();
    }
    
    private void initViews() {
        etEmail = findViewById(R.id.etEmail);
        etLogin = findViewById(R.id.etLogin);
        etPassword = findViewById(R.id.etPassword);
        etPasswordConfirm = findViewById(R.id.etPasswordConfirm);
        btnRegister = findViewById(R.id.btnRegister);
        tvLogin = findViewById(R.id.tvLogin);
        progressBar = findViewById(R.id.progressBar);
    }
    
    private void setupListeners() {
        btnRegister.setOnClickListener(v -> attemptRegister());
        
        tvLogin.setOnClickListener(v -> {
            finish(); // Retour à la page de connexion
        });
    }
    
    private void attemptRegister() {
        String email = etEmail.getText().toString().trim();
        String login = etLogin.getText().toString().trim();
        String password = etPassword.getText().toString();
        String passwordConfirm = etPasswordConfirm.getText().toString();
        
        // Validation
        if (email.isEmpty()) {
            etEmail.setError("Email requis");
            etEmail.requestFocus();
            return;
        }
        
        if (!android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
            etEmail.setError("Email invalide");
            etEmail.requestFocus();
            return;
        }
        
        if (login.isEmpty()) {
            etLogin.setError("Login requis");
            etLogin.requestFocus();
            return;
        }
        
        if (login.length() < 3) {
            etLogin.setError("Login trop court (min 3 caractères)");
            etLogin.requestFocus();
            return;
        }
        
        if (password.isEmpty()) {
            etPassword.setError("Mot de passe requis");
            etPassword.requestFocus();
            return;
        }
        
        if (password.length() < 6) {
            etPassword.setError("Mot de passe trop court (min 6 caractères)");
            etPassword.requestFocus();
            return;
        }
        
        if (!password.equals(passwordConfirm)) {
            etPasswordConfirm.setError("Les mots de passe ne correspondent pas");
            etPasswordConfirm.requestFocus();
            return;
        }
        
        // Afficher le chargement
        setLoading(true);
        
        // Utiliser l'API HTTP au lieu de JDBC
        AuthApiClient.register(email, login, password, new AuthApiClient.RegisterCallback() {
            @Override
            public void onSuccess(String message) {
                setLoading(false);
                Toast.makeText(RegisterActivity.this, "Inscription réussie ! Connectez-vous.", Toast.LENGTH_SHORT).show();
                finish(); // Retour à la page de connexion
            }
            
            @Override
            public void onError(String message) {
                setLoading(false);
                Toast.makeText(RegisterActivity.this, message, Toast.LENGTH_LONG).show();
            }
        });
    }
    
    private void setLoading(boolean loading) {
        progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        btnRegister.setEnabled(!loading);
        etEmail.setEnabled(!loading);
        etLogin.setEnabled(!loading);
        etPassword.setEnabled(!loading);
        etPasswordConfirm.setEnabled(!loading);
    }
}
