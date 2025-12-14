package com.example.homesecure;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.util.Log;
import android.view.WindowManager;
import android.os.Build;
import android.content.res.Configuration;
import android.webkit.ConsoleMessage;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

import java.io.BufferedInputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class CameraActivity extends AppCompatActivity {

    private static final String TAG = "CameraActivity";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_camera);

        // Fullscreen (better immersion for video)
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        setupLiveFeed();

        boolean isAlert = getIntent().getBooleanExtra("EXTRA_ALERT", false);
        LinearLayout layoutActions = findViewById(R.id.layoutAlertActions);

        if (isAlert) {
            layoutActions.setVisibility(View.VISIBLE);
        }

        findViewById(R.id.btnFalseAlarm).setOnClickListener(v -> sendFeedback(false));

        findViewById(R.id.btnRealThreat).setOnClickListener(v -> sendFeedback(true));
    }

    private void setupLiveFeed() {
        SharedPreferences sharedPref = getSharedPreferences("HomeSecurePrefs", Context.MODE_PRIVATE);
        String ip = sharedPref.getString("RP_IP", null);
        String port = sharedPref.getString("RP_PORT", "");

        TextView tvStatus = findViewById(R.id.tvLiveFeedStatus);

        WebView webView = findViewById(R.id.wvLiveFeed);

        // Permet d'inspecter la console WebView depuis Chrome DevTools (si app debuggable)
        try {
            WebView.setWebContentsDebuggingEnabled(true);
        } catch (Exception ignored) {
        }

        WebSettings settings = webView.getSettings();
        // WebRTC in WebView requires JavaScript.
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setLoadsImagesAutomatically(true);
        settings.setBlockNetworkImage(false);
        settings.setCacheMode(WebSettings.LOAD_NO_CACHE);
        settings.setMediaPlaybackRequiresUserGesture(false);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }

        webView.clearCache(true);
        webView.clearHistory();

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                Log.w(TAG, "WebView error " + errorCode + ": " + description + " url=" + failingUrl);
                showStatus(tvStatus, "Erreur WebView: " + description + "\n" + failingUrl);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                // On cache l'overlay mais on va vérifier si WebRTC est supporté.
                hideStatus(tvStatus);

                // Diagnostic: est-ce que RTCPeerConnection existe dans ce WebView ?
                try {
                    view.evaluateJavascript("typeof RTCPeerConnection", value -> {
                        // value est une string JSON (ex: \"function\" ou \"undefined\")
                        if (value != null && value.contains("undefined")) {
                            showStatus(tvStatus,
                                    "WebRTC non supporté par ce WebView.\n" +
                                            "Mets à jour \"Android System WebView\" et Chrome sur le téléphone.");
                        }
                    });
                } catch (Exception e) {
                    Log.w(TAG, "evaluateJavascript failed", e);
                }
                super.onPageFinished(view, url);
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onConsoleMessage(ConsoleMessage consoleMessage) {
                if (consoleMessage == null) return super.onConsoleMessage(consoleMessage);
                String msg = consoleMessage.message();
                Log.i(TAG, "JS: " + msg + " (" + consoleMessage.sourceId() + ":" + consoleMessage.lineNumber() + ")");

                // Affiche seulement les erreurs pour ne pas masquer la vidéo.
                if (consoleMessage.messageLevel() == ConsoleMessage.MessageLevel.ERROR) {
                    showStatus(tvStatus, "Erreur WebRTC: " + msg);
                }
                return super.onConsoleMessage(consoleMessage);
            }

            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                // Par précaution: certains WebView demandent des permissions même en recv-only.
                if (request == null) return;
                runOnUiThread(() -> {
                    try {
                        request.grant(request.getResources());
                    } catch (Exception e) {
                        Log.w(TAG, "PermissionRequest grant failed", e);
                    }
                });
            }
        });

        if (ip == null || ip.isEmpty()) {
            Toast.makeText(this, "IP non configurée (Settings)", Toast.LENGTH_LONG).show();
            showStatus(tvStatus, "IP non configurée (Settings)");
            return;
        }

        // Compat: si l'ancien champ IP contenait déjà "IP:PORT".
        if ((port == null || port.isEmpty()) && ip.contains(":")) {
            String[] parts = ip.split(":", 2);
            ip = parts[0];
            port = parts.length > 1 ? parts[1] : "";
        }

        String finalPort = (port == null || port.isEmpty()) ? "8080" : port;
        String baseUrl = "http://" + ip + ":" + finalPort;

        // 1) Ping /health pour vérifier qu'une requête atteint vraiment le serveur
        showStatus(tvStatus, "Connexion au flux...\n" + baseUrl);
        runHealthCheck(baseUrl + "/health", tvStatus);

        // 2) Charger la page WebRTC (faible latence)
        String webrtcUrl = baseUrl + "/webrtc";
        Log.i(TAG, "Loading live feed: " + webrtcUrl);
        showStatus(tvStatus, "Chargement...\n" + webrtcUrl);
        webView.loadUrl(webrtcUrl);
    }

    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        // Ne pas recharger la page: on garde la session WebRTC.
        WebView webView = findViewById(R.id.wvLiveFeed);
        if (webView != null) {
            webView.requestLayout();
        }
    }

    private void runHealthCheck(String healthUrl, TextView tvStatus) {
        new Thread(() -> {
            boolean ok = false;
            String error = null;
            HttpURLConnection conn = null;
            try {
                URL url = new URL(healthUrl);
                conn = (HttpURLConnection) url.openConnection();
                conn.setConnectTimeout(2500);
                conn.setReadTimeout(2500);
                conn.setRequestMethod("GET");
                conn.setUseCaches(false);
                int code = conn.getResponseCode();
                ok = (code >= 200 && code < 300);

                // Drain a bit to complete request properly
                try (BufferedInputStream in = new BufferedInputStream(conn.getInputStream())) {
                    byte[] buf = new byte[64];
                    //noinspection StatementWithEmptyBody
                    while (in.read(buf) != -1) {
                        break;
                    }
                }
            } catch (Exception e) {
                error = e.getClass().getSimpleName() + ": " + e.getMessage();
                Log.w(TAG, "Health check failed: " + healthUrl, e);
            } finally {
                if (conn != null) {
                    try {
                        conn.disconnect();
                    } catch (Exception ignored) {
                    }
                }
            }

            boolean finalOk = ok;
            String finalError = error;
            runOnUiThread(() -> {
                if (finalOk) {
                    Toast.makeText(this, "Serveur caméra OK", Toast.LENGTH_SHORT).show();
                    hideStatus(tvStatus);
                } else {
                    String msg = "Impossible d'atteindre le serveur caméra.\n" + healthUrl;
                    if (finalError != null) {
                        msg += "\n" + finalError;
                    }
                    showStatus(tvStatus, msg);
                }
            });
        }).start();
    }

    private void showStatus(TextView tv, String message) {
        if (tv == null) return;
        tv.setText(message);
        tv.setVisibility(View.VISIBLE);
    }

    private void hideStatus(TextView tv) {
        if (tv == null) return;
        tv.setVisibility(View.GONE);
    }

    private void sendFeedback(boolean isRealThreat) {
        SharedPreferences sharedPref = getSharedPreferences("HomeSecurePrefs", Context.MODE_PRIVATE);
        String ip = sharedPref.getString("RP_IP", "Unknown");

        // Mock sending data back to Raspberry Pi
        String status = isRealThreat ? "CONFIRMED THREAT" : "FALSE ALARM";

        Toast.makeText(this, "Sending '" + status + "' to " + ip + "...", Toast.LENGTH_LONG).show();

        // Simulate network delay then close
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            Toast.makeText(this, "Response Logged by System.", Toast.LENGTH_SHORT).show();
            finish();
        }, 1500);
    }
}