# 🔍 Debugging Guide - Authentication with Logs

Esta guía te ayudará a interpretar los logs y solucionar problemas de autenticación.

## 🚀 Cómo Ver los Logs

```bash
# Si usas Docker
docker-compose logs -f api

# Si usas local
# Los logs aparecerán en la terminal donde ejecutaste uvicorn
```

## 📝 Interpretación de Logs

### ✅ Login Exitoso (Lo que DEBES ver)

```
📥 Incoming request: POST /api/auth/google
   Origin: http://localhost:3005
   User-Agent: Mozilla/5.0...
   🍪 No cookies in request
   🔑 No Authorization header

🔑 Login attempt for user: jmartincastroa@gmail.com
✅ JWT token generated for user jmartincastroa@gmail.com (ID: 1)
🎫 Token preview: eyJhbGciOiJIUzI1NiIsInR5cCI6...
🍪 Auth cookie set for user jmartincastroa@gmail.com
   - Cookie name: auth_token
   - HttpOnly: True
   - SameSite: lax
   - Secure: False
   - Max-Age: 604800 seconds

📤 Response: 200 for POST /api/auth/google
   🍪 Setting cookie in response
```

**Qué significa:**
- ✅ Login exitoso
- ✅ Cookie establecida en la respuesta
- ✅ El navegador debería guardar la cookie

---

### ✅ Request Autenticado Exitoso (Con Cookie)

```
📥 Incoming request: GET /api/bot/state/ETHUSDT
   Origin: http://localhost:3005
   User-Agent: Mozilla/5.0...
   🍪 Cookies present: ['auth_token']
   🍪 auth_token: eyJhbGciOiJIUzI1NiIsInR5cCI6...
   🔑 No Authorization header

🔐 Auth check for: GET /api/bot/state/ETHUSDT
📨 Headers: {'host': 'localhost:5000', 'origin': 'http://localhost:3005', ...}
🍪 Cookies: {'auth_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6...'}
✅ Token found in Cookie: eyJhbGciOiJIUzI1NiIsInR5cCI6...
🔍 Verifying token from Cookie...
✅ Token verified successfully. Payload: {'user_id': 1, 'firebase_uid': 'xxx', 'email': 'user@email.com', ...}
✅ User authenticated: user@email.com (ID: 1)

📤 Response: 200 for GET /api/bot/state/ETHUSDT
```

**Qué significa:**
- ✅ Cookie enviada correctamente desde el frontend
- ✅ Token válido
- ✅ Usuario autenticado
- ✅ Request procesado exitosamente

---

### ❌ Problema 1: Cookie NO se envía (403 Forbidden)

```
📥 Incoming request: GET /api/bot/state/ETHUSDT
   Origin: http://localhost:3005
   User-Agent: Mozilla/5.0...
   🍪 No cookies in request          ← ❌ PROBLEMA AQUÍ
   🔑 No Authorization header

🔐 Auth check for: GET /api/bot/state/ETHUSDT
📨 Headers: {'host': 'localhost:5000', 'origin': 'http://localhost:3005', ...}
🍪 Cookies: {}                        ← ❌ VACÍO
❌ No token found in request
   - Authorization header: Not present
   - Cookies: []

📤 Response: 401 for GET /api/bot/state/ETHUSDT
```

**Diagnóstico:**
- ❌ El navegador NO está enviando la cookie
- ❌ Falta `withCredentials: true` en el frontend

**Solución:**

```javascript
// En tu apiClient.js
const axiosClient = axios.create({
  baseURL: 'http://localhost:5000/api',
  withCredentials: true,  // ← AGREGAR ESTO
  headers: {
    'Content-Type': 'application/json'
  }
});

// ELIMINAR el interceptor que intenta leer la cookie
// NO hagas esto:
// const token = Cookies.get('auth_token');
```

---

### ❌ Problema 2: Token Inválido o Expirado

```
📥 Incoming request: GET /api/bot/state/ETHUSDT
   🍪 Cookies present: ['auth_token']
   🍪 auth_token: eyJhbGciOiJIUzI1NiIsInR5cCI6...

🔐 Auth check for: GET /api/bot/state/ETHUSDT
✅ Token found in Cookie: eyJhbGciOiJIUzI1NiIsInR5cCI6...
🔍 Verifying token from Cookie...
❌ Token verification failed for token from Cookie  ← ❌ PROBLEMA

📤 Response: 401 for GET /api/bot/state/ETHUSDT
```

**Diagnóstico:**
- ❌ El token ha expirado o es inválido
- ❌ Puede ser que el JWT_SECRET_KEY cambió

**Solución:**

```javascript
// Hacer logout y login de nuevo
await authService.logout();
await authService.loginWithGoogle();
```

---

### ❌ Problema 3: Cookie Se Envía Pero Con Nombre Incorrecto

```
📥 Incoming request: GET /api/bot/state/ETHUSDT
   🍪 Cookies present: ['some_other_cookie']  ← ❌ No 'auth_token'
   🔑 No Authorization header

❌ No token found in request
   - Cookies: ['some_other_cookie']
```

**Diagnóstico:**
- ❌ Hay cookies, pero no la cookie `auth_token`
- ❌ Posible problema de dominio/path

**Solución:**

Verificar en DevTools → Application → Cookies que la cookie `auth_token` existe para `localhost:5000`.

---

### ❌ Problema 4: Frontend Envía Authorization Header (Incorrecto)

```
📥 Incoming request: GET /api/bot/state/ETHUSDT
   🍪 No cookies in request
   🔑 Authorization header: Bearer undefined...  ← ❌ 'undefined'

🔐 Auth check for: GET /api/bot/state/ETHUSDT
✅ Token found in Authorization header: undefined...
🔍 Verifying token from Authorization header...
❌ Token verification failed for token from Authorization header
```

**Diagnóstico:**
- ❌ El frontend está intentando enviar un token en el header
- ❌ El token es `undefined` porque no puede leer la cookie HttpOnly
- ❌ El interceptor de axios está intentando hacer `Cookies.get('auth_token')`

**Solución:**

```javascript
// ELIMINAR este interceptor de apiClient.js
axiosClient.interceptors.request.use(
  (config) => {
    const token = Cookies.get('auth_token');  // ← ELIMINAR TODO ESTO
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  }
);

// NO es necesario, withCredentials: true es suficiente
```

---

## 🧪 Checklist de Debugging

Sigue estos pasos en orden:

### 1️⃣ Hacer Login

```bash
# Ver logs después del login
docker-compose logs api | grep -A 20 "Login attempt"
```

**Busca:**
- [ ] `✅ JWT token generated`
- [ ] `🍪 Auth cookie set`
- [ ] `📤 Response: 200`
- [ ] `🍪 Setting cookie in response`

---

### 2️⃣ Verificar Cookie en Navegador

1. **Abre DevTools** → **Application** → **Cookies** → `http://localhost:5000`
2. **Busca cookie** `auth_token`

**Debe tener:**
- [ ] **Name**: `auth_token`
- [ ] **Value**: Un JWT largo (eyJhbGci...)
- [ ] **Domain**: `localhost` o vacío
- [ ] **Path**: `/`
- [ ] **HttpOnly**: ✅
- [ ] **Secure**: ❌ (en desarrollo)
- [ ] **SameSite**: `Lax`

---

### 3️⃣ Hacer Request Protegido

```bash
# Ver logs del request
docker-compose logs api | grep -A 30 "bot/state"
```

**Busca:**
- [ ] `🍪 Cookies present: ['auth_token']`
- [ ] `✅ Token found in Cookie`
- [ ] `✅ Token verified successfully`
- [ ] `✅ User authenticated`
- [ ] `📤 Response: 200`

---

### 4️⃣ Verificar Headers en DevTools

1. **DevTools** → **Network Tab**
2. Click en el request `/api/bot/state/ETHUSDT`

**Request Headers debe tener:**
- [ ] `Cookie: auth_token=eyJhbGci...`
- [ ] `Origin: http://localhost:3005`

**NO debe tener:**
- [ ] ❌ `Authorization: Bearer undefined`

---

## 🔧 Soluciones Rápidas por Síntoma

| Síntoma | Causa | Solución |
|---------|-------|----------|
| 403 Forbidden + "No cookies in request" | Falta `withCredentials: true` | Agregar en axios/fetch |
| 401 + "Token verification failed" | Token expirado/inválido | Logout y login de nuevo |
| Cookie presente pero 401 | JWT_SECRET_KEY cambió | Reconstruir backend y re-login |
| `Authorization: Bearer undefined` | Interceptor leyendo cookie HttpOnly | Eliminar interceptor |
| Cookie no aparece en DevTools | SameSite=Strict | Ya corregido (usa Lax) |
| OPTIONS request 403 | CORS preflight | Ya configurado correctamente |

---

## 📊 Logs de Ejemplo Completo (Flujo Exitoso)

```
# 1. LOGIN
📥 Incoming request: POST /api/auth/google
   🍪 No cookies in request
🔑 Login attempt for user: user@example.com
✅ JWT token generated for user user@example.com (ID: 1)
🍪 Auth cookie set for user user@example.com
📤 Response: 200 for POST /api/auth/google
   🍪 Setting cookie in response

# 2. GET BOT STATE
📥 Incoming request: GET /api/bot/state/ETHUSDT
   🍪 Cookies present: ['auth_token']
   🍪 auth_token: eyJhbGciOiJIUzI1NiIsInR5cCI6...
🔐 Auth check for: GET /api/bot/state/ETHUSDT
✅ Token found in Cookie: eyJhbGciOiJIUzI1NiIsInR5cCI6...
🔍 Verifying token from Cookie...
✅ Token verified successfully
✅ User authenticated: user@example.com (ID: 1)
📤 Response: 200 for GET /api/bot/state/ETHUSDT

# 3. GET TRADES
📥 Incoming request: GET /api/bot/trades/recent/ETHUSDT
   🍪 Cookies present: ['auth_token']
✅ Token found in Cookie
✅ User authenticated: user@example.com (ID: 1)
📤 Response: 200 for GET /api/bot/trades/recent/ETHUSDT
```

---

## 🎯 Próximos Pasos

1. **Reconstruir backend con logs**:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **Ver logs en tiempo real**:
   ```bash
   docker-compose logs -f api
   ```

3. **Hacer login desde el frontend**

4. **Compartir los logs** completos del login + primer request protegido

5. **Verificar en DevTools** que la cookie existe

---

**Con estos logs detallados, podemos identificar exactamente dónde está el problema.**
