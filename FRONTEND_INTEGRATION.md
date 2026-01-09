# 🔗 Frontend Integration Guide

Esta guía explica cómo integrar el frontend con la API para que la autenticación con cookies funcione correctamente.

## 🍪 Problema: Cookies no se envían en requests

Si después del login exitoso, los requests protegidos reciben **403 Forbidden**, es porque **las cookies no se están enviando** desde el frontend.

## ✅ Solución: Configurar `credentials: 'include'`

### 1. **Usando Fetch API**

```javascript
// ❌ INCORRECTO - Las cookies NO se envían
fetch('http://localhost:5000/api/bot/state/ETHUSDT', {
  headers: {
    'Content-Type': 'application/json',
  }
})

// ✅ CORRECTO - Las cookies SÍ se envían
fetch('http://localhost:5000/api/bot/state/ETHUSDT', {
  method: 'GET',
  credentials: 'include',  // ← IMPORTANTE
  headers: {
    'Content-Type': 'application/json',
  }
})
```

### 2. **Usando Axios**

```javascript
import axios from 'axios';

// Configurar axios globalmente
const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  withCredentials: true,  // ← IMPORTANTE
  headers: {
    'Content-Type': 'application/json',
  }
});

// Usar en todas las requests
api.get('/bot/state/ETHUSDT');
api.post('/auth/google', data);
```

### 3. **Usando React Query con Axios**

```javascript
import axios from 'axios';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  }
});

// En tus queries
const { data } = useQuery({
  queryKey: ['botState', 'ETHUSDT'],
  queryFn: () => api.get('/bot/state/ETHUSDT').then(res => res.data)
});
```

## 📝 Ejemplo Completo: Autenticación

### Login con Google Firebase

```javascript
// src/services/authService.js
import axios from 'axios';
import { signInWithPopup } from 'firebase/auth';
import { auth, googleProvider } from '../firebase/config';

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  withCredentials: true,  // ← Habilitar cookies
  headers: {
    'Content-Type': 'application/json',
  }
});

export const loginWithGoogle = async () => {
  try {
    // 1. Autenticar con Firebase
    const result = await signInWithPopup(auth, googleProvider);

    // 2. Obtener ID token de Firebase
    const idToken = await result.user.getIdToken();

    // 3. Enviar al backend
    const response = await api.post('/auth/google', {
      idToken: idToken,
      email: result.user.email,
      displayName: result.user.displayName,
      photoURL: result.user.photoURL,
      uid: result.user.uid
    });

    // 4. La cookie se establece automáticamente por el backend
    console.log('Login successful:', response.data);

    return response.data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

export const logout = async () => {
  try {
    // Llamar al endpoint de logout (limpia la cookie)
    await api.post('/auth/logout');

    // Logout de Firebase también
    await auth.signOut();

    console.log('Logout successful');
  } catch (error) {
    console.error('Logout error:', error);
    throw error;
  }
};

export const validateToken = async () => {
  try {
    const response = await api.get('/auth/validate');
    return response.data;
  } catch (error) {
    console.error('Token validation error:', error);
    return null;
  }
};
```

### Protected Routes / Auth Guard

```javascript
// src/components/ProtectedRoute.jsx
import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { validateToken } from '../services/authService';

export const ProtectedRoute = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const result = await validateToken();
        setIsAuthenticated(result?.valid === true);
      } catch (error) {
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};
```

### Fetch Bot Data

```javascript
// src/services/botService.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  withCredentials: true,  // ← IMPORTANTE
});

export const getBotState = async (pair) => {
  const response = await api.get(`/bot/state/${pair}`);
  return response.data;
};

export const getRecentTrades = async (pair, limit = 10) => {
  const response = await api.get(`/bot/trades/recent/${pair}`, {
    params: { limit }
  });
  return response.data;
};

export const getPerformance = async (pair = null) => {
  const response = await api.get('/bot/performance', {
    params: pair ? { pair } : {}
  });
  return response.data;
};
```

### React Component Example

```javascript
// src/pages/Dashboard.jsx
import { useQuery } from '@tanstack/react-query';
import { getBotState, getRecentTrades } from '../services/botService';

export const Dashboard = () => {
  const { data: botState, isLoading: loadingState } = useQuery({
    queryKey: ['botState', 'ETHUSDT'],
    queryFn: () => getBotState('ETHUSDT'),
    refetchInterval: 5000, // Refetch every 5 seconds
  });

  const { data: recentTrades, isLoading: loadingTrades } = useQuery({
    queryKey: ['recentTrades', 'ETHUSDT'],
    queryFn: () => getRecentTrades('ETHUSDT'),
  });

  if (loadingState || loadingTrades) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h1>Bot Dashboard</h1>

      <div>
        <h2>Current State</h2>
        <p>In Position: {botState.data.in_position ? 'Yes' : 'No'}</p>
        <p>Current Price: ${botState.data.current_price}</p>
        <p>PnL: ${botState.data.pnl_usd}</p>
      </div>

      <div>
        <h2>Recent Trades</h2>
        <ul>
          {recentTrades.data.map(trade => (
            <li key={trade.id}>
              {trade.pair} - PnL: ${trade.pnl_usd}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
```

## 🔍 Debugging: Verificar Cookies

### En el Navegador (DevTools)

1. **Abre DevTools** → **Network Tab**
2. Haz login
3. Busca el request a `/api/auth/google`
4. En **Response Headers** deberías ver:
   ```
   Set-Cookie: auth_token=eyJ0eXAiOiJKV1QiLCJ...; HttpOnly; Path=/; SameSite=Lax
   ```

5. En los **requests posteriores**, en **Request Headers** deberías ver:
   ```
   Cookie: auth_token=eyJ0eXAiOiJKV1QiLCJ...
   ```

### Verificar en Application Tab

1. **DevTools** → **Application Tab** → **Cookies**
2. Selecciona `http://localhost:5000`
3. Deberías ver la cookie `auth_token` con:
   - **HttpOnly**: ✅
   - **SameSite**: `Lax` (desarrollo) o `None` (producción)
   - **Secure**: ❌ (desarrollo) o ✅ (producción)

## ⚠️ Problemas Comunes

### 1. "Cookies no aparecen en DevTools"

**Causa**: Falta `withCredentials: true` en axios o `credentials: 'include'` en fetch.

**Solución**: Agregar en todas las configuraciones de cliente HTTP.

### 2. "403 Forbidden después de login exitoso"

**Causa**: Las cookies no se están enviando en requests subsecuentes.

**Solución**:
- Verificar `withCredentials: true` en axios
- Verificar que el backend tenga `allow_credentials=True` en CORS
- Verificar que `SameSite` sea `Lax` o `None`

### 3. "Cookie se establece pero no se envía"

**Causa**: `SameSite=Strict` bloqueando cookies cross-origin.

**Solución**: El backend ya usa `SameSite=Lax` para desarrollo. Si usas producción con HTTPS, usa `SameSite=None` con `Secure=True`.

### 4. "CORS error"

**Causa**: El origen del frontend no está en `ALLOWED_ORIGINS`.

**Solución**:
```env
# En el .env del backend
ALLOWED_ORIGINS=http://localhost:3005,http://localhost:3000
```

## 🚀 Checklist de Integración

- [ ] Backend configurado con `ALLOWED_ORIGINS` correcto
- [ ] Backend usa `SameSite=Lax` (desarrollo) o `SameSite=None` con HTTPS (producción)
- [ ] Frontend usa `withCredentials: true` (axios) o `credentials: 'include'` (fetch)
- [ ] Login exitoso retorna 200 OK
- [ ] Cookie `auth_token` aparece en DevTools → Application → Cookies
- [ ] Requests subsecuentes envían la cookie en el header `Cookie:`
- [ ] Requests protegidos retornan 200 OK (no 403)

## 📚 Referencias

- [MDN: HTTP Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies)
- [MDN: Fetch API Credentials](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch#sending_a_request_with_credentials_included)
- [Axios: withCredentials](https://axios-http.com/docs/req_config)
- [SameSite Cookie Attribute](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite)

---

**¿Problemas?** Verifica los logs del backend con `docker-compose logs -f api` y los headers en DevTools.
