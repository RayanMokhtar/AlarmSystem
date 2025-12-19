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

import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;
import androidx.annotation.Nullable;

public class CameraActivity extends AppCompatActivity {

    private static final String TAG = "CameraActivity";
    
    // Modes de streaming
    private static final String MODE_AUTO = "auto";
    private static final String MODE_WEBRTC = "webrtc";
    private static final String MODE_MJPEG = "mjpeg";
    
    // MJPEG par défaut car plus compatible (fonctionne sans internet)
    private String currentMode = MODE_MJPEG;
    private String baseUrl = "";
    private WebView webView;
    private TextView tvStatus;
    
    // WebSocket pour les commandes de contrôle
    private OkHttpClient wsClient;
    private WebSocket webSocket;
    private boolean isWebSocketConnected = false;
    private String activeDirection = null;
    
    // Pour l'envoi continu des commandes
    private Handler directionHandler = new Handler(Looper.getMainLooper());
    private boolean isSendingDirection = false;
    
    // Pour gérer les déconnexions dans les cas spéciaux
    private Handler disconnectHandler = new Handler(Looper.getMainLooper());
    private Runnable delayedDisconnect = null;
    private boolean isActivityActive = true;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_camera);

        // Fullscreen (better immersion for video)
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        isActivityActive = true;
        setupLiveFeed();

        boolean isAlert = getIntent().getBooleanExtra("EXTRA_ALERT", false);
        LinearLayout layoutActions = findViewById(R.id.layoutAlertActions);

        if (isAlert) {
            layoutActions.setVisibility(View.VISIBLE);
        }

        findViewById(R.id.btnFalseAlarm).setOnClickListener(v -> sendFeedback(false));

        findViewById(R.id.btnRealThreat).setOnClickListener(v -> sendFeedback(true));
        
        // Setup directional controls
        setupDirectionalControls();
    }

    @Override
    protected void onResume() {
        super.onResume();
        isActivityActive = true;
        // Annuler toute déconnexion différée si l'activité redevient active
        if (delayedDisconnect != null) {
            disconnectHandler.removeCallbacks(delayedDisconnect);
            delayedDisconnect = null;
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        isActivityActive = false;
        // Programmer une déconnexion différée au cas où l'activité ne reviendrait pas
        delayedDisconnect = () -> {
            if (!isActivityActive) {
                Log.i(TAG, "Activity paused for too long, sending disconnect notification");
                notifyDisconnect();
            }
        };
        // Délai de 30 secondes avant de considérer que c'est une vraie déconnexion
        disconnectHandler.postDelayed(delayedDisconnect, 30000);
    }

    @Override
    protected void onStop() {
        super.onStop();
        // Ici on pourrait ajouter une logique supplémentaire si nécessaire
        // Mais onPause gère déjà le cas principal
    }
    
    private void setupDirectionalControls() {
        // Correction: boutons envoient leur direction logique
        setupContinuousButton(R.id.btnUp, "up");
        setupContinuousButton(R.id.btnDown, "down");
        setupContinuousButton(R.id.btnLeft, "left");
        setupContinuousButton(R.id.btnRight, "right");
    }
    
    private void setupContinuousButton(int buttonId, String direction) {
        findViewById(buttonId).setOnTouchListener((v, event) -> {
            switch (event.getAction()) {
                case android.view.MotionEvent.ACTION_DOWN:
                    // Commencer l'envoi en continu
                    startContinuousDirectionSend(direction);
                    v.setPressed(true);
                    return true;
                    
                case android.view.MotionEvent.ACTION_UP:
                case android.view.MotionEvent.ACTION_CANCEL:
                    // Arrêter l'envoi
                    stopContinuousDirectionSend();
                    v.setPressed(false);
                    return true;
            }
            return false;
        });
    }
    
    private void startContinuousDirectionSend(String direction) {
        if (isSendingDirection) {
            return; // Déjà en cours
        }
        
        activeDirection = direction;
        isSendingDirection = true;
        
        // Envoyer la première commande immédiatement
        sendDirectionViaWebSocket(direction);
        
        // Puis envoyer en boucle toutes les 150ms tant que le bouton est appuyé
        directionHandler.postDelayed(new Runnable() {
            @Override
            public void run() {
                if (isSendingDirection && direction.equals(activeDirection)) {
                    sendDirectionViaWebSocket(direction);
                    directionHandler.postDelayed(this, 150); // Répéter toutes les 150ms
                }
            }
        }, 150);
    }
    
    private void stopContinuousDirectionSend() {
        isSendingDirection = false;
        activeDirection = null;
        directionHandler.removeCallbacksAndMessages(null); // Arrêter toutes les répétitions
    }
    
    private void sendDirectionViaWebSocket(String direction) {
        if (webSocket != null && isWebSocketConnected) {
            try {
                webSocket.send(direction);
                Log.d(TAG, "Commande envoyée via WebSocket: " + direction);
            } catch (Exception e) {
                Log.e(TAG, "Erreur envoi WebSocket: " + e.getMessage());
            }
        } else {
            Log.w(TAG, "WebSocket non connecté, tentative de reconnexion...");
            connectWebSocket();
        }
    }
    
    private void connectWebSocket() {
        if (baseUrl == null || baseUrl.isEmpty()) {
            Log.e(TAG, "baseUrl non défini");
            return;
        }
        
        // Fermer l'ancienne connexion si elle existe
        if (webSocket != null) {
            try {
                webSocket.close(1000, "Reconnexion");
            } catch (Exception ignored) {}
        }
        
        String wsUrl = baseUrl.replace("http://", "ws://").replace("https://", "wss://") + "/ws/control";
        Log.i(TAG, "Connexion WebSocket: " + wsUrl);
        
        if (wsClient == null) {
            wsClient = new OkHttpClient.Builder()
                .pingInterval(30, java.util.concurrent.TimeUnit.SECONDS)
                .build();
        }
        
        Request request = new Request.Builder()
            .url(wsUrl)
            .build();
        
        webSocket = wsClient.newWebSocket(request, new WebSocketListener() {
            @Override
            public void onOpen(@Nullable WebSocket webSocket, @Nullable Response response) {
                isWebSocketConnected = true;
                Log.i(TAG, "WebSocket connecté");
                runOnUiThread(() -> 
                    Toast.makeText(CameraActivity.this, "Contrôles connectés", Toast.LENGTH_SHORT).show()
                );
            }
            
            @Override
            public void onMessage(@Nullable WebSocket webSocket, @Nullable String text) {
                Log.d(TAG, "Message WebSocket: " + text);
            }
            
            @Override
            public void onClosing(@Nullable WebSocket webSocket, int code, @Nullable String reason) {
                isWebSocketConnected = false;
                Log.i(TAG, "WebSocket fermeture: " + reason);
            }
            
            @Override
            public void onClosed(@Nullable WebSocket webSocket, int code, @Nullable String reason) {
                isWebSocketConnected = false;
                Log.i(TAG, "WebSocket fermé: " + reason);
            }
            
            @Override
            public void onFailure(@Nullable WebSocket webSocket, @Nullable Throwable t, @Nullable Response response) {
                isWebSocketConnected = false;
                Log.e(TAG, "Erreur WebSocket: " + (t != null ? t.getMessage() : "unknown"));
                runOnUiThread(() -> 
                    Toast.makeText(CameraActivity.this, "Erreur connexion contrôles", Toast.LENGTH_SHORT).show()
                );
            }
        });
    }

    private void setupLiveFeed() {
        SharedPreferences sharedPref = getSharedPreferences("HomeSecurePrefs", Context.MODE_PRIVATE);
        String ip = sharedPref.getString("RP_IP", null);
        String port = sharedPref.getString("RP_PORT", "");
        currentMode = sharedPref.getString("STREAMING_MODE", MODE_AUTO);

        tvStatus = findViewById(R.id.tvLiveFeedStatus);
        webView = findViewById(R.id.wvLiveFeed);

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
        
        // Force WebView to expose real IP addresses instead of mDNS (.local)
        // This is critical for WebRTC to work with aiortc server
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                settings.setOffscreenPreRaster(true);
            }
            // Disable mDNS obfuscation via command line flag
            webView.getSettings().setUserAgentString(
                webView.getSettings().getUserAgentString() + " WebRTC-DisableMDNS"
            );
        } catch (Exception e) {
            Log.w(TAG, "Could not disable mDNS: " + e.getMessage());
        }

        webView.clearCache(true);
        webView.clearHistory();

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                Log.w(TAG, "WebView error " + errorCode + ": " + description + " url=" + failingUrl);
                
                // En mode auto, si WebRTC échoue, basculer vers MJPEG
                if (currentMode.equals(MODE_AUTO) && failingUrl != null && failingUrl.contains("/webrtc")) {
                    Log.i(TAG, "WebRTC failed, falling back to MJPEG");
                    loadMjpegFeed();
                } else {
                    showStatus("Erreur WebView: " + description + "\n" + failingUrl);
                }
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                hideStatus();

                // Si on charge WebRTC, vérifier que RTCPeerConnection est supporté
                if (url != null && url.contains("/webrtc")) {
                    try {
                        view.evaluateJavascript("typeof RTCPeerConnection", value -> {
                            if (value != null && value.contains("undefined")) {
                                if (currentMode.equals(MODE_AUTO)) {
                                    Log.i(TAG, "WebRTC not supported, falling back to MJPEG");
                                    runOnUiThread(() -> loadMjpegFeed());
                                } else {
                                    showStatus("WebRTC non supporté par ce WebView.\nMets à jour \"Android System WebView\" et Chrome.");
                                }
                            }
                        });
                    } catch (Exception e) {
                        Log.w(TAG, "evaluateJavascript failed", e);
                    }
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

                // Détecter les erreurs ICE pour basculer vers MJPEG en mode auto
                if (msg != null && msg.contains("ICE failed") && currentMode.equals(MODE_AUTO)) {
                    Log.i(TAG, "ICE failed detected, falling back to MJPEG");
                    runOnUiThread(() -> loadMjpegFeed());
                    return super.onConsoleMessage(consoleMessage);
                }

                // Affiche seulement les erreurs pour ne pas masquer la vidéo.
                if (consoleMessage.messageLevel() == ConsoleMessage.MessageLevel.ERROR) {
                    // Ne pas afficher les erreurs ICE en mode auto (on bascule vers MJPEG)
                    if (currentMode.equals(MODE_AUTO) && msg != null && msg.contains("ICE")) {
                        return super.onConsoleMessage(consoleMessage);
                    }
                    showStatus("Erreur: " + msg);
                }
                return super.onConsoleMessage(consoleMessage);
            }

            @Override
            public void onPermissionRequest(final PermissionRequest request) {
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
            showStatus("IP non configurée (Settings)");
            return;
        }

        // Compat: si l'ancien champ IP contenait déjà "IP:PORT".
        if ((port == null || port.isEmpty()) && ip.contains(":")) {
            String[] parts = ip.split(":", 2);
            ip = parts[0];
            port = parts.length > 1 ? parts[1] : "";
        }

        String finalPort = (port == null || port.isEmpty()) ? "8080" : port;
        baseUrl = "http://" + ip + ":" + finalPort;
        // Établir la connexion WebSocket pour les contrôles
        connectWebSocket();
        // 1) Ping /health pour vérifier qu'une requête atteint vraiment le serveur
        showStatus("Connexion au flux...\n" + baseUrl);
        runHealthCheck(baseUrl + "/health");

        // 2) Charger le flux selon le mode choisi
        loadStreamByMode();
    }
    
    private void loadStreamByMode() {
        switch (currentMode) {
            case MODE_MJPEG:
                loadMjpegFeed();
                break;
            case MODE_WEBRTC:
                loadWebRtcFeed();
                break;
            case MODE_AUTO:
            default:
                // En mode auto, essayer WebRTC d'abord
                loadWebRtcFeed();
                break;
        }
    }
    
    private void loadWebRtcFeed() {
        String webrtcUrl = baseUrl + "/webrtc";
        Log.i(TAG, "Loading WebRTC feed: " + webrtcUrl);
        showStatus("Chargement WebRTC...\n" + webrtcUrl);
        webView.loadUrl(webrtcUrl);
    }
    
    private void loadMjpegFeed() {
        String mjpegUrl = baseUrl + "/mobile";
        Log.i(TAG, "Loading MJPEG feed: " + mjpegUrl);
        showStatus("Chargement MJPEG...\n" + mjpegUrl);
        
        // Pour MJPEG, on charge une page HTML simple avec une balise <img>
        String html = "<!DOCTYPE html><html><head>" +
                "<meta name='viewport' content='width=device-width, initial-scale=1, viewport-fit=cover'>" +
                "<style>" +
                "html,body{margin:0;padding:0;background:#000;height:100%;overflow:hidden}" +
                "img{width:100vw;height:100vh;object-fit:contain}" +
                ".hud{position:fixed;left:12px;right:12px;bottom:12px;color:#fff;font:12px system-ui;" +
                "background:rgba(0,0,0,.55);border-radius:12px;padding:10px 12px}" +
                "</style></head><body>" +
                "<img src='" + baseUrl + "/video_feed' alt='Live Feed'>" +
                "<div class='hud'>Mode: <strong>MJPEG</strong> · URL: <code>" + baseUrl + "/video_feed</code></div>" +
                "</body></html>";
        
        webView.loadDataWithBaseURL(baseUrl, html, "text/html", "UTF-8", null);
    }

    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        // Ne pas recharger la page: on garde la session.
        if (webView != null) {
            webView.requestLayout();
        }
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        isActivityActive = false;

        // Annuler toute déconnexion différée
        if (delayedDisconnect != null) {
            disconnectHandler.removeCallbacks(delayedDisconnect);
            delayedDisconnect = null;
        }

        // Arrêter l'envoi continu des directions
        stopContinuousDirectionSend();
        // Fermer la connexion WebSocket proprement
        if (webSocket != null) {
            try {
                webSocket.close(1000, "Activity destroyed");
            } catch (Exception ignored) {}
        }
        if (wsClient != null) {
            try {
                wsClient.dispatcher().executorService().shutdown();
            } catch (Exception ignored) {}
        }
        // Notify Raspberry Pi of disconnect
        notifyDisconnect();
    }

    private void runHealthCheck(String healthUrl) {
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
                    hideStatus();
                } else {
                    String msg = "Impossible d'atteindre le serveur caméra.\n" + healthUrl;
                    if (finalError != null) {
                        msg += "\n" + finalError;
                    }
                    showStatus(msg);
                }
            });
        }).start();
    }

    private void showStatus(String message) {
        if (tvStatus == null) return;
        tvStatus.setText(message);
        tvStatus.setVisibility(View.VISIBLE);
    }

    private void hideStatus() {
        if (tvStatus == null) return;
        tvStatus.setVisibility(View.GONE);
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

    private void notifyDisconnect() {
        new Thread(() -> {
            try {
                SharedPreferences sharedPref = getSharedPreferences("HomeSecurePrefs", Context.MODE_PRIVATE);
                String ip = sharedPref.getString("RP_IP", null);
                String port = sharedPref.getString("RP_PORT", "");

                if (ip == null || ip.isEmpty()) {
                    Log.e(TAG, "Cannot send disconnect notification: IP not configured");
                    return;
                }

                // Compat: si l'ancien champ IP contenait déjà "IP:PORT".
                if ((port == null || port.isEmpty()) && ip.contains(":")) {
                    String[] parts = ip.split(":", 2);
                    ip = parts[0];
                    port = parts.length > 1 ? parts[1] : "";
                }

                String finalPort = (port == null || port.isEmpty()) ? "8080" : port;
                String disconnectUrl = "http://" + ip + ":" + finalPort + "/disconnect";

                OkHttpClient client = new OkHttpClient();
                Request request = new Request.Builder()
                        .url(disconnectUrl)
                        .post(RequestBody.create("", MediaType.parse("application/json")))
                        .build();
                Response response = client.newCall(request).execute();
                if (response.isSuccessful()) {
                    Log.d(TAG, "Disconnect notification sent successfully to " + disconnectUrl);
                } else {
                    Log.e(TAG, "Failed to send disconnect notification: " + response.code());
                }
                response.close();
            } catch (Exception e) {
                Log.e(TAG, "Error sending disconnect notification", e);
            }
        }).start();
    }
}