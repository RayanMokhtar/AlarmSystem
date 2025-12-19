# 🔍 Guide de Débogage - Système d'Authentification

## ⚠️ Problèmes Actuels

1. **L'application crash après ajout de l'inscription/connexion**
2. **Les données ne s'insèrent pas dans la base de données**
3. **L'app crash lors de la connexion**

---

## ✅ Améliorations Apportées

### 1. **Logging Complet dans DatabaseHelper.java**

Tous les logs sont tagués avec `"DatabaseHelper"` :

```java
// Connexion
Log.d(TAG, "Tentative de connexion à: " + url);
Log.d(TAG, "Connexion réussie !");

// Login
Log.d(TAG, "Tentative de login pour: " + loginOrEmail);
Log.d(TAG, "Exécution de la requête login...");
Log.d(TAG, "Login réussi pour: " + user.login);

// Register
Log.d(TAG, "Tentative d'inscription pour: " + login + " / " + email);
Log.d(TAG, "Insertion de l'utilisateur...");
Log.d(TAG, "Inscription réussie ! Utilisateur ID: " + userId);

// Test
Log.d(TAG, "Test de connexion à la base...");
Log.d(TAG, "Test connexion: OK/FAILED");
```

### 2. **Gestion d'Erreur Améliorée**

- **try-catch dans toutes les méthodes** avec `printStackTrace()`
- **finally blocks** pour fermer les connexions proprement
- **Affichage des erreurs** dans les Toast

### 3. **Test de Connexion Automatique**

Avant chaque tentative de login/register, l'app teste d'abord la connexion DB :

```java
boolean dbConnected = DatabaseHelper.testConnection();
if (!dbConnected) {
    Toast.makeText(this, "Impossible de se connecter à la base de données. Vérifiez DatabaseConfig.", Toast.LENGTH_LONG).show();
    return;
}
```

### 4. **Application Class (HomeSecureApplication.java)**

- **StrictMode désactivé** : Permet les opérations réseau (temporaire, pour debug)
- **Driver PostgreSQL chargé** au démarrage de l'app

---

## 🛠️ Étapes de Débogage

### **ÉTAPE 1 : Vérifier DatabaseConfig.java**

Ouvrez le fichier et **assurez-vous que les credentials sont corrects** :

```java
public class DatabaseConfig {
    public static final String DB_HOST = "VOTRE_IP_OU_HOSTNAME";
    public static final String DB_PORT = "5432";
    public static final String DB_NAME = "hammal_aterlierrt";
    public static final String DB_USER = "VOTRE_USER";
    public static final String DB_PASSWORD = "VOTRE_PASSWORD";
}
```

**Points de vérification** :
- ✅ `DB_HOST` : L'adresse IP du serveur PostgreSQL (ex: `192.168.1.100` ou `localhost`)
- ✅ `DB_PORT` : Généralement `5432`
- ✅ `DB_NAME` : Le nom de votre base de données
- ✅ `DB_USER` : Le nom d'utilisateur PostgreSQL
- ✅ `DB_PASSWORD` : Le mot de passe (sans guillemets supplémentaires)

---

### **ÉTAPE 2 : Rebuild Complet**

1. **Clean Project** : `Build` → `Clean Project`
2. **Rebuild Project** : `Build` → `Rebuild Project`
3. Attendez la fin du build (barre de progression en bas)

---

### **ÉTAPE 3 : Ouvrir Logcat**

1. **Ouvrez Logcat** : `View` → `Tool Windows` → `Logcat`
2. **Filtrez par tag** : Dans la barre de recherche, tapez : `tag:DatabaseHelper`
3. **Ou filtrez par app** : Sélectionnez `com.example.homesecure` dans le dropdown

---

### **ÉTAPE 4 : Lancer l'App et Observer**

1. **Run sur émulateur ou device** : Cliquez sur le bouton ▶️ (Run)
2. **Observer les logs** au démarrage :
   ```
   D/HomeSecureApp: Application démarrée
   D/HomeSecureApp: Driver PostgreSQL chargé avec succès
   ```

---

### **ÉTAPE 5 : Tester l'Inscription**

1. Sur l'écran de **Login**, cliquez sur **"Pas encore de compte ? Inscrivez-vous"**
2. Remplissez le formulaire :
   - Email : `test@example.com`
   - Login : `testuser`
   - Mot de passe : `123456`
   - Confirmation : `123456`
3. Cliquez sur **"S'inscrire"**
4. **Observez Logcat** :

**✅ Succès attendu** :
```
D/DatabaseHelper: Test de connexion à la base...
D/DatabaseHelper: Connexion réussie !
D/DatabaseHelper: Test connexion: OK
D/DatabaseHelper: Tentative d'inscription pour: testuser / test@example.com
D/DatabaseHelper: Insertion de l'utilisateur...
D/DatabaseHelper: Inscription réussie ! Utilisateur ID: [uuid]
```

**❌ Erreur possible 1 - Connexion échouée** :
```
E/DatabaseHelper: Erreur connexion DB: SQLException - Connection refused
```
→ **Solution** : PostgreSQL n'est pas accessible. Vérifiez l'IP et le firewall.

**❌ Erreur possible 2 - Credentials incorrects** :
```
E/DatabaseHelper: Erreur connexion DB: PSQLException - FATAL: password authentication failed
```
→ **Solution** : Mauvais username ou password dans DatabaseConfig.java

**❌ Erreur possible 3 - Réseau** :
```
E/DatabaseHelper: Erreur connexion DB: UnknownHostException - Unable to resolve host
```
→ **Solution** : L'adresse DB_HOST est incorrecte ou le device n'a pas accès réseau.

---

### **ÉTAPE 6 : Vérifier dans PostgreSQL**

Si l'inscription réussit, vérifiez dans PostgreSQL :

```sql
SELECT * FROM utilisateur WHERE login = 'testuser';
```

Vous devriez voir :
```
utilisateur_id | email              | login    | motdepasse | date_creation
---------------|--------------------|-----------|-----------|-----------------
[uuid]         | test@example.com   | testuser  | 123456     | 2025-01-XX
```

---

### **ÉTAPE 7 : Tester la Connexion**

1. Sur l'écran de **Login**, entrez :
   - Login/Email : `testuser`
   - Mot de passe : `123456`
2. Cliquez sur **"Se connecter"**
3. **Observez Logcat** :

**✅ Succès attendu** :
```
D/DatabaseHelper: Test de connexion à la base...
D/DatabaseHelper: Test connexion: OK
D/DatabaseHelper: Tentative de login pour: testuser
D/DatabaseHelper: Exécution de la requête login...
D/DatabaseHelper: Login réussi pour: testuser
```

**❌ Erreur possible - Login invalide** :
```
D/DatabaseHelper: Aucun utilisateur trouvé
```
→ **Solution** : Vérifiez que l'utilisateur existe dans la base avec le bon mot de passe.

---

## 🔥 Erreurs Critiques Possibles

### **1. NetworkOnMainThreadException**

**Symptôme** : Crash avec `NetworkOnMainThreadException` dans les logs.

**Solution** : ✅ Déjà résolu avec `HomeSecureApplication.java` qui désactive StrictMode.

---

### **2. ClassNotFoundException: org.postgresql.Driver**

**Symptôme** :
```
E/HomeSecureApp: Erreur chargement driver PostgreSQL
java.lang.ClassNotFoundException: org.postgresql.Driver
```

**Solution** :
1. Vérifiez `build.gradle.kts` :
   ```kotlin
   dependencies {
       implementation("org.postgresql:postgresql:42.7.1")
   }
   ```
2. Sync Gradle : `File` → `Sync Project with Gradle Files`
3. Rebuild

---

### **3. Timeout de Connexion**

**Symptôme** :
```
E/DatabaseHelper: Erreur connexion DB: SocketTimeoutException
```

**Solution** :
- PostgreSQL autorise les connexions externes ? Éditez `postgresql.conf` :
  ```
  listen_addresses = '*'
  ```
- Le firewall autorise le port 5432 ? :
  ```bash
  sudo ufw allow 5432/tcp
  ```
- Éditez `pg_hba.conf` pour autoriser votre IP :
  ```
  host    all    all    0.0.0.0/0    md5
  ```

---

### **4. UUID Non Généré**

**Symptôme** :
```
E/DatabaseHelper: Aucune ligne insérée
```

**Solution** : Vérifiez que la table utilise bien `gen_random_uuid()` :
```sql
ALTER TABLE utilisateur ALTER COLUMN utilisateur_id SET DEFAULT gen_random_uuid();
```

---

## 📋 Checklist de Résolution

- [ ] DatabaseConfig.java complété avec les vrais credentials
- [ ] Build → Clean Project → Rebuild Project
- [ ] Émulateur/Device connecté
- [ ] Logcat ouvert avec filtre `tag:DatabaseHelper`
- [ ] PostgreSQL accessible depuis le réseau
- [ ] Firewall autorise le port 5432
- [ ] Table `utilisateur` existe avec la bonne structure
- [ ] Driver PostgreSQL chargé (log `Driver PostgreSQL chargé avec succès`)
- [ ] Test de connexion OK avant login/register
- [ ] Inscription réussie avec UUID dans les logs
- [ ] Connexion réussie avec redirection vers MainActivity

---

## 🚀 Commandes PostgreSQL Utiles

### Vérifier que PostgreSQL écoute :
```bash
netstat -an | grep 5432
```

### Tester la connexion depuis le terminal :
```bash
psql -h 192.168.1.100 -U votre_user -d hammal_aterlierrt
```

### Vérifier la structure de la table :
```sql
\d utilisateur
```

### Lister tous les utilisateurs :
```sql
SELECT * FROM utilisateur;
```

### Supprimer un utilisateur de test :
```sql
DELETE FROM utilisateur WHERE login = 'testuser';
```

---

## 📞 Si Tout Échoue

**Copiez et partagez les logs complets** :

1. Dans Logcat, cliquez sur une ligne d'erreur
2. Ctrl+C pour copier
3. Partagez le stack trace complet qui commence par :
   ```
   E/DatabaseHelper: Erreur [methode]: [exception]
   [stack trace complet]
   ```

Avec ces informations, on pourra identifier précisément le problème !
