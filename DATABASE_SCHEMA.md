# 🗄️ Database Schema Reference

Este documento describe el schema de base de datos esperado por la API.

> **Nota**: Esta API se conecta a una base de datos existente. Este schema es solo una referencia de las tablas y columnas que la API espera encontrar.

## 📋 Tablas

### 1. users

Almacena información de usuarios autenticados con Firebase.

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    firebase_uid VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    photo_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_firebase_uid (firebase_uid),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Columnas**:
- `id`: ID único del usuario (auto-incremento)
- `firebase_uid`: UID de Firebase (único)
- `email`: Email del usuario
- `name`: Nombre del usuario
- `photo_url`: URL de la foto de perfil
- `created_at`: Fecha de creación
- `updated_at`: Fecha de última actualización

---

### 2. api_configurations

Almacena las API keys de Binance encriptadas.

```sql
CREATE TABLE api_configurations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    environment ENUM('testnet', 'production') NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    api_secret_encrypted TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_env (user_id, environment),
    INDEX idx_user_env (user_id, environment)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Columnas**:
- `id`: ID único de la configuración
- `user_id`: ID del usuario (foreign key a `users`)
- `environment`: Entorno (`testnet` o `production`)
- `api_key_encrypted`: API key de Binance encriptada (AES-256)
- `api_secret_encrypted`: Secret key de Binance encriptada (AES-256)
- `created_at`: Fecha de creación
- `updated_at`: Fecha de última actualización

**Constraints**:
- Única combinación de `user_id` + `environment`

---

### 3. bot_configurations

Configuración del bot de trading por usuario, par y entorno.

```sql
CREATE TABLE bot_configurations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pair ENUM('ETHUSDT', 'BTCUSDT') NOT NULL,
    environment ENUM('testnet', 'production') NOT NULL,
    stop_loss_percent DECIMAL(5,2) DEFAULT 4.5,
    position_size_percent DECIMAL(5,2) DEFAULT 50.0,
    take_profit_1_percent DECIMAL(5,2) DEFAULT 5.0,
    take_profit_2_percent DECIMAL(5,2) DEFAULT 7.5,
    take_profit_3_percent DECIMAL(5,2) DEFAULT 10.0,
    buy_threshold DECIMAL(3,2) DEFAULT 0.6,
    regime_filter_enabled BOOLEAN DEFAULT TRUE,
    adaptive_threshold BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_pair_env (user_id, pair, environment),
    INDEX idx_user_pair_env (user_id, pair, environment)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Columnas**:
- `id`: ID único de la configuración
- `user_id`: ID del usuario
- `pair`: Par de trading (`ETHUSDT` o `BTCUSDT`)
- `environment`: Entorno (`testnet` o `production`)
- `stop_loss_percent`: Porcentaje de stop loss
- `position_size_percent`: Porcentaje del capital a usar por operación
- `take_profit_1_percent`: Porcentaje del primer take profit
- `take_profit_2_percent`: Porcentaje del segundo take profit
- `take_profit_3_percent`: Porcentaje del tercer take profit
- `buy_threshold`: Umbral de probabilidad para comprar
- `regime_filter_enabled`: Si está habilitado el filtro de régimen de mercado
- `adaptive_threshold`: Si está habilitado el umbral adaptativo
- `is_active`: Si el bot está activo para este par
- `created_at`: Fecha de creación
- `updated_at`: Fecha de última actualización

---

### 4. bot_states

Estado actual del bot por usuario y par.

```sql
CREATE TABLE bot_states (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pair ENUM('ETHUSDT', 'BTCUSDT') NOT NULL,
    environment ENUM('testnet', 'production') NOT NULL,
    in_position BOOLEAN DEFAULT FALSE,
    entry_price DECIMAL(18,8),
    entry_time TIMESTAMP NULL,
    current_price DECIMAL(18,8),
    position_amount DECIMAL(18,8),
    position_original DECIMAL(18,8),
    tp1_executed BOOLEAN DEFAULT FALSE,
    tp2_executed BOOLEAN DEFAULT FALSE,
    tp3_executed BOOLEAN DEFAULT FALSE,
    pnl_usd DECIMAL(18,8),
    pnl_percent DECIMAL(10,4),
    stop_loss_price DECIMAL(18,8),
    stop_loss_percent DECIMAL(5,2),
    tp1_price DECIMAL(18,8),
    tp1_percent DECIMAL(5,2),
    tp2_price DECIMAL(18,8),
    tp2_percent DECIMAL(5,2),
    tp3_price DECIMAL(18,8),
    tp3_percent DECIMAL(5,2),
    regime VARCHAR(50),
    probability DECIMAL(5,4),
    volatility DECIMAL(10,4),
    available_capital DECIMAL(18,8),
    total_pnl DECIMAL(18,8),
    total_pnl_percent DECIMAL(10,4),
    total_trades INT DEFAULT 0,
    winning_trades INT DEFAULT 0,
    blocked_trades INT DEFAULT 0,
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_pair (user_id, pair),
    INDEX idx_last_check (last_check)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Columnas**:
- `id`: ID único del estado
- `user_id`: ID del usuario
- `pair`: Par de trading
- `environment`: Entorno
- `in_position`: Si está actualmente en una posición
- `entry_price`: Precio de entrada de la posición actual
- `entry_time`: Timestamp de entrada
- `current_price`: Precio actual del activo
- `position_amount`: Cantidad actual en la posición
- `position_original`: Cantidad original de la posición
- `tp1_executed`, `tp2_executed`, `tp3_executed`: Si se ejecutaron los take profits
- `pnl_usd`: P&L en USD de la posición actual
- `pnl_percent`: P&L en porcentaje
- `stop_loss_price`, `tp1_price`, `tp2_price`, `tp3_price`: Precios de SL y TPs
- `stop_loss_percent`, `tp1_percent`, `tp2_percent`, `tp3_percent`: Porcentajes configurados
- `regime`: Régimen del mercado (BULL, BEAR, NEUTRAL)
- `probability`: Probabilidad de compra del modelo
- `volatility`: Volatilidad actual del mercado
- `available_capital`: Capital disponible
- `total_pnl`: P&L total acumulado
- `total_pnl_percent`: P&L total en porcentaje
- `total_trades`: Número total de trades
- `winning_trades`: Número de trades ganadores
- `blocked_trades`: Número de trades bloqueados
- `last_check`: Última actualización del estado

---

### 5. trades

Historial de trades ejecutados.

```sql
CREATE TABLE trades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pair ENUM('ETHUSDT', 'BTCUSDT') NOT NULL,
    environment ENUM('testnet', 'production') NOT NULL,
    entry_price DECIMAL(18,8) NOT NULL,
    exit_price DECIMAL(18,8),
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP NULL,
    amount DECIMAL(18,8) NOT NULL,
    pnl_usd DECIMAL(18,8),
    pnl_percent DECIMAL(10,4),
    exit_reason VARCHAR(50),
    status ENUM('OPEN', 'CLOSED', 'CANCELLED') DEFAULT 'OPEN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_pair (user_id, pair),
    INDEX idx_status (status),
    INDEX idx_exit_time (exit_time),
    INDEX idx_entry_time (entry_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Columnas**:
- `id`: ID único del trade
- `user_id`: ID del usuario
- `pair`: Par de trading
- `environment`: Entorno
- `entry_price`: Precio de entrada
- `exit_price`: Precio de salida
- `entry_time`: Timestamp de entrada
- `exit_time`: Timestamp de salida
- `amount`: Cantidad del trade
- `pnl_usd`: P&L en USD
- `pnl_percent`: P&L en porcentaje
- `exit_reason`: Razón de salida (TP1, TP2, TP3, SL, MANUAL)
- `status`: Estado del trade (OPEN, CLOSED, CANCELLED)
- `created_at`: Fecha de creación del registro

---

### 6. docker_containers

Estado de los contenedores Docker del bot.

```sql
CREATE TABLE docker_containers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    environment ENUM('testnet', 'production') NOT NULL,
    container_id VARCHAR(255),
    status ENUM('running', 'stopped', 'restarting', 'error') DEFAULT 'stopped',
    last_restart TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_env (user_id, environment)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Columnas**:
- `id`: ID único del contenedor
- `user_id`: ID del usuario
- `environment`: Entorno
- `container_id`: ID del contenedor Docker
- `status`: Estado del contenedor (running, stopped, restarting, error)
- `last_restart`: Timestamp del último reinicio
- `created_at`: Fecha de creación
- `updated_at`: Fecha de última actualización

---

## 🔗 Relaciones

```
users (1) ----< (N) api_configurations
users (1) ----< (N) bot_configurations
users (1) ----< (N) bot_states
users (1) ----< (N) trades
users (1) ----< (N) docker_containers
```

---

## 📝 Notas Importantes

1. **Encriptación**: Las columnas `api_key_encrypted` y `api_secret_encrypted` contienen datos encriptados con AES-256. El backend se encarga de encriptar/desencriptar.

2. **Índices**: Se han agregado índices para optimizar las queries más frecuentes:
   - Búsqueda por usuario + par
   - Búsqueda por estado
   - Ordenamiento por fechas

3. **Foreign Keys**: Todas las tablas tienen `ON DELETE CASCADE` para limpiar automáticamente los datos relacionados cuando se elimina un usuario.

4. **Decimals**: Se usan DECIMAL en lugar de FLOAT para mayor precisión en valores monetarios.

5. **Timestamps**: Todas las tablas tienen `created_at` y `updated_at` para auditoría.

6. **ENUMs**: Se usan ENUMs para restringir valores válidos:
   - `environment`: 'testnet' o 'production'
   - `pair`: 'ETHUSDT' o 'BTCUSDT'
   - `status`: Depende de la tabla

---

## 🚀 Script de Creación Completo

```sql
-- Crear base de datos
CREATE DATABASE IF NOT EXISTS trading_bot
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE trading_bot;

-- Tabla users
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    firebase_uid VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    photo_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_firebase_uid (firebase_uid),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla api_configurations
CREATE TABLE api_configurations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    environment ENUM('testnet', 'production') NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    api_secret_encrypted TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_env (user_id, environment),
    INDEX idx_user_env (user_id, environment)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla bot_configurations
CREATE TABLE bot_configurations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pair ENUM('ETHUSDT', 'BTCUSDT') NOT NULL,
    environment ENUM('testnet', 'production') NOT NULL,
    stop_loss_percent DECIMAL(5,2) DEFAULT 4.5,
    position_size_percent DECIMAL(5,2) DEFAULT 50.0,
    take_profit_1_percent DECIMAL(5,2) DEFAULT 5.0,
    take_profit_2_percent DECIMAL(5,2) DEFAULT 7.5,
    take_profit_3_percent DECIMAL(5,2) DEFAULT 10.0,
    buy_threshold DECIMAL(3,2) DEFAULT 0.6,
    regime_filter_enabled BOOLEAN DEFAULT TRUE,
    adaptive_threshold BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_pair_env (user_id, pair, environment),
    INDEX idx_user_pair_env (user_id, pair, environment)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla bot_states
CREATE TABLE bot_states (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pair ENUM('ETHUSDT', 'BTCUSDT') NOT NULL,
    environment ENUM('testnet', 'production') NOT NULL,
    in_position BOOLEAN DEFAULT FALSE,
    entry_price DECIMAL(18,8),
    entry_time TIMESTAMP NULL,
    current_price DECIMAL(18,8),
    position_amount DECIMAL(18,8),
    position_original DECIMAL(18,8),
    tp1_executed BOOLEAN DEFAULT FALSE,
    tp2_executed BOOLEAN DEFAULT FALSE,
    tp3_executed BOOLEAN DEFAULT FALSE,
    pnl_usd DECIMAL(18,8),
    pnl_percent DECIMAL(10,4),
    stop_loss_price DECIMAL(18,8),
    stop_loss_percent DECIMAL(5,2),
    tp1_price DECIMAL(18,8),
    tp1_percent DECIMAL(5,2),
    tp2_price DECIMAL(18,8),
    tp2_percent DECIMAL(5,2),
    tp3_price DECIMAL(18,8),
    tp3_percent DECIMAL(5,2),
    regime VARCHAR(50),
    probability DECIMAL(5,4),
    volatility DECIMAL(10,4),
    available_capital DECIMAL(18,8),
    total_pnl DECIMAL(18,8),
    total_pnl_percent DECIMAL(10,4),
    total_trades INT DEFAULT 0,
    winning_trades INT DEFAULT 0,
    blocked_trades INT DEFAULT 0,
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_pair (user_id, pair),
    INDEX idx_last_check (last_check)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla trades
CREATE TABLE trades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pair ENUM('ETHUSDT', 'BTCUSDT') NOT NULL,
    environment ENUM('testnet', 'production') NOT NULL,
    entry_price DECIMAL(18,8) NOT NULL,
    exit_price DECIMAL(18,8),
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP NULL,
    amount DECIMAL(18,8) NOT NULL,
    pnl_usd DECIMAL(18,8),
    pnl_percent DECIMAL(10,4),
    exit_reason VARCHAR(50),
    status ENUM('OPEN', 'CLOSED', 'CANCELLED') DEFAULT 'OPEN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_pair (user_id, pair),
    INDEX idx_status (status),
    INDEX idx_exit_time (exit_time),
    INDEX idx_entry_time (entry_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla docker_containers
CREATE TABLE docker_containers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    environment ENUM('testnet', 'production') NOT NULL,
    container_id VARCHAR(255),
    status ENUM('running', 'stopped', 'restarting', 'error') DEFAULT 'stopped',
    last_restart TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_env (user_id, environment)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## ✅ Verificación

Después de crear las tablas, verifica:

```sql
-- Ver todas las tablas
SHOW TABLES;

-- Verificar estructura de cada tabla
DESCRIBE users;
DESCRIBE api_configurations;
DESCRIBE bot_configurations;
DESCRIBE bot_states;
DESCRIBE trades;
DESCRIBE docker_containers;

-- Verificar índices
SHOW INDEX FROM users;
SHOW INDEX FROM trades;

-- Verificar foreign keys
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'trading_bot'
AND REFERENCED_TABLE_NAME IS NOT NULL;
```

---

**Este schema está optimizado para las operaciones de la API.**
