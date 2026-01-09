# 🔥 Firebase Setup - Guía Paso a Paso

Esta guía detalla cómo obtener las credenciales de Firebase necesarias para el backend.

## 📋 Requisitos

- Cuenta de Google
- Proyecto de Firebase creado (o crear uno nuevo)

## 🎯 Paso 1: Crear/Acceder a Proyecto Firebase

### Crear Nuevo Proyecto

1. Ve a [Firebase Console](https://console.firebase.google.com/)
2. Click en **"Add project"** o **"Crear proyecto"**
3. Ingresa un nombre para tu proyecto (ej: `trading-bot-api`)
4. (Opcional) Habilita Google Analytics
5. Click en **"Create project"**

### Acceder a Proyecto Existente

1. Ve a [Firebase Console](https://console.firebase.google.com/)
2. Selecciona tu proyecto de la lista

## 🔐 Paso 2: Habilitar Autenticación con Google

1. En el panel izquierdo, click en **"Authentication"** o **"Autenticación"**
2. Click en **"Get Started"** si es la primera vez
3. Ve a la pestaña **"Sign-in method"** o **"Método de inicio de sesión"**
4. Encuentra **"Google"** en la lista de proveedores
5. Click en **"Google"** para editar
6. **Habilita** el toggle
7. Selecciona un **email de soporte** del proyecto
8. Click en **"Save"** o **"Guardar"**

## 🔑 Paso 3: Obtener Service Account Credentials (Para Backend)

### Método Completo

1. En Firebase Console, click en el ícono de ⚙️ (Settings/Configuración)
2. Selecciona **"Project settings"** o **"Configuración del proyecto"**
3. Ve a la pestaña **"Service accounts"** o **"Cuentas de servicio"**
4. Asegúrate de estar en la opción **"Firebase Admin SDK"**
5. Selecciona el lenguaje **"Python"**
6. Click en **"Generate new private key"** o **"Generar nueva clave privada"**
7. Confirma en el modal de advertencia
8. Se descargará un archivo JSON (ej: `trading-bot-api-firebase-adminsdk-xxxxx.json`)

### Contenido del Archivo

El archivo JSON descargado contiene algo como esto:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "xxxxxxxxxxxxxxxxxxxxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\nXXXXXXXXXXXXXXX\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com",
  "client_id": "xxxxxxxxxxxxxxxxxxxxx",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40your-project-id.iam.gserviceaccount.com"
}
```

## 📝 Paso 4: Configurar Credenciales en el Backend

### Opción A: Usar Archivo (Desarrollo Local)

```bash
# 1. Renombrar el archivo descargado
mv trading-bot-api-firebase-adminsdk-xxxxx.json firebase-credentials.json

# 2. Mover al directorio del proyecto
cp firebase-credentials.json /path/to/api_bot_trading_ia/

# 3. Configurar .env
echo "FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json" >> .env
```

### Opción B: Usar String JSON (Producción/Docker)

```bash
# 1. Convertir JSON a string de una línea
cat firebase-credentials.json | jq -c . > firebase-oneline.json

# 2. Copiar el contenido y pegarlo en .env (escapando comillas)
FIREBASE_CREDENTIALS_JSON='{"type":"service_account","project_id":"your-project-id",...}'
```

**Script Helper para convertir:**

```bash
#!/bin/bash
# convert-firebase-json.sh

if [ -z "$1" ]; then
    echo "Usage: ./convert-firebase-json.sh <firebase-credentials.json>"
    exit 1
fi

echo "FIREBASE_CREDENTIALS_JSON='"$(cat $1 | jq -c .)"'"
```

Uso:
```bash
chmod +x convert-firebase-json.sh
./convert-firebase-json.sh firebase-credentials.json >> .env
```

## 🌐 Paso 5: Obtener Configuración Web (Para Frontend)

1. En Firebase Console, ⚙️ > **"Project settings"**
2. Scroll down hasta **"Your apps"** o **"Tus apps"**
3. Si no tienes una app web, click en el ícono `</>` para agregar una
4. Ingresa un nombre para la app (ej: `Trading Bot Web`)
5. Click en **"Register app"** o **"Registrar app"**
6. Copia la configuración de Firebase:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  authDomain: "your-project-id.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project-id.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:xxxxxxxxxxxxxx"
};
```

7. Pega esta configuración en tu frontend React:

```javascript
// src/firebase/config.js
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  authDomain: "your-project-id.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project-id.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:xxxxxxxxxxxxxx"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
```

## ✅ Paso 6: Verificar la Configuración

### Test Backend

```bash
# 1. Iniciar el servidor
uvicorn app.main:app --reload

# 2. Check health endpoint
curl http://localhost:5000/health

# 3. Verificar logs
# Deberías ver: "Firebase initialized successfully"
```

### Test Frontend Login

```javascript
// src/components/Login.jsx
import { signInWithPopup } from 'firebase/auth';
import { auth, googleProvider } from '../firebase/config';

const handleGoogleLogin = async () => {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    const idToken = await result.user.getIdToken();

    // Enviar al backend
    const response = await fetch('http://localhost:5000/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        idToken: idToken,
        email: result.user.email,
        displayName: result.user.displayName,
        photoURL: result.user.photoURL,
        uid: result.user.uid
      })
    });

    const data = await response.json();
    console.log('Login successful:', data);
  } catch (error) {
    console.error('Login error:', error);
  }
};
```

## 🔒 Seguridad

### ⚠️ IMPORTANTE - No Commitear Credenciales

```bash
# Asegúrate de que firebase-credentials.json está en .gitignore
echo "firebase-credentials.json" >> .gitignore
echo "*-firebase-*.json" >> .gitignore

# Verificar que no está trackeado
git status
```

### 🛡️ Restringir API Keys (Recomendado para Producción)

1. En Firebase Console, ⚙️ > **"Project settings"**
2. Ve a la pestaña **"Service accounts"**
3. Click en **"Manage permissions"** en IAM
4. Configura roles específicos para el service account
5. Limita los permisos solo a lo necesario

### 🌐 Configurar Dominios Autorizados

1. En Firebase Console, **"Authentication"**
2. Ve a la pestaña **"Settings"** o **"Configuración"**
3. Scroll hasta **"Authorized domains"** o **"Dominios autorizados"**
4. Agrega tus dominios:
   - `localhost` (para desarrollo)
   - `tu-dominio.com` (para producción)

## 🐛 Troubleshooting

### Error: "Firebase is not initialized"

**Causa**: El archivo de credenciales no se encuentra o el JSON es inválido

**Solución**:
```bash
# Verificar que el archivo existe
ls -la firebase-credentials.json

# Verificar que el JSON es válido
cat firebase-credentials.json | jq .

# Verificar la variable de entorno
echo $FIREBASE_CREDENTIALS_PATH
```

### Error: "Invalid Firebase credentials"

**Causa**: El service account key es incorrecto o ha sido revocado

**Solución**:
1. Genera una nueva clave en Firebase Console
2. Reemplaza el archivo `firebase-credentials.json`
3. Reinicia el servidor

### Error: "Permission denied"

**Causa**: El service account no tiene permisos suficientes

**Solución**:
1. Ve a [IAM Console](https://console.cloud.google.com/iam-admin/iam)
2. Encuentra el service account de Firebase
3. Agrega el rol **"Firebase Admin"**

### Error: "auth/invalid-id-token"

**Causa**: El token de Firebase del frontend está expirado o es inválido

**Solución**:
```javascript
// Refrescar el token en el frontend
const user = auth.currentUser;
if (user) {
  const freshToken = await user.getIdToken(true); // force refresh
  // Usar freshToken
}
```

## 📚 Referencias

- [Firebase Admin SDK Setup](https://firebase.google.com/docs/admin/setup)
- [Firebase Authentication](https://firebase.google.com/docs/auth)
- [Service Account Keys](https://cloud.google.com/iam/docs/creating-managing-service-account-keys)

## ✅ Checklist Final

- [ ] Proyecto de Firebase creado
- [ ] Autenticación con Google habilitada
- [ ] Service account credentials descargadas
- [ ] Archivo `firebase-credentials.json` en el proyecto
- [ ] Variable `FIREBASE_CREDENTIALS_PATH` o `FIREBASE_CREDENTIALS_JSON` configurada en `.env`
- [ ] Archivo agregado a `.gitignore`
- [ ] Servidor backend iniciado correctamente
- [ ] Log "Firebase initialized successfully" visible
- [ ] Frontend puede obtener ID token
- [ ] Endpoint `/api/auth/google` funciona correctamente

---

**¡Listo! Tu autenticación con Firebase está configurada.**
