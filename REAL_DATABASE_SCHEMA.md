# 🗄️ Real Database Schema - Complete Reference

Este documento contiene el schema **real y completo** de la base de datos, extraído directamente de la base de datos en producción.

## 📋 Tablas Implementadas en la API

### 1. users ✅
```sql
CREATE TABLE `users` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `firebase_uid` VARCHAR(128) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `name` VARCHAR(100) NULL DEFAULT NULL,
    `photo_url` TEXT NULL DEFAULT NULL,
    `created_at` TIMESTAMP NULL DEFAULT current_timestamp(),
    `last_login` TIMESTAMP NULL DEFAULT NULL,
    `is_active` TINYINT(1) NULL DEFAULT '1',
    PRIMARY KEY (`id`),
    UNIQUE INDEX `firebase_uid` (`firebase_uid`),
    UNIQUE INDEX `email` (`email`),
    INDEX `idx_email` (`email`),
    INDEX `idx_firebase_uid` (`firebase_uid`)
) ENGINE=InnoDB COLLATE='utf8mb4_unicode_ci';
```

**API Status:** ✅ Completamente implementado
- Login/logout
- Token refresh
- Validation

---

### 2. bot_states ✅
```sql
CREATE TABLE `bot_states` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` INT(11) NOT NULL,
    `pair` VARCHAR(20) NOT NULL,
    `environment` ENUM('testnet','production') NOT NULL,
    `in_position` TINYINT(1) NULL DEFAULT '0',
    `entry_price` DECIMAL(18,8) NULL DEFAULT NULL,
    `entry_time` TIMESTAMP NULL DEFAULT NULL,
    `current_price` DECIMAL(18,8) NULL DEFAULT NULL,
    `position_amount` DECIMAL(18,8) NULL DEFAULT NULL,
    `position_original` DECIMAL(18,8) NULL DEFAULT NULL,
    `tp1_executed` TINYINT(1) NULL DEFAULT '0',
    `tp2_executed` TINYINT(1) NULL DEFAULT '0',
    `current_pnl_usd` DECIMAL(18,2) NULL DEFAULT NULL,
    `current_pnl_percent` DECIMAL(8,4) NULL DEFAULT NULL,
    `regime` ENUM('BULL','BEAR','NEUTRAL','LATERAL','UNKNOWN') NULL DEFAULT 'UNKNOWN',
    `probability` DECIMAL(5,4) NULL DEFAULT NULL,
    `volatility` DECIMAL(6,2) NULL DEFAULT NULL,
    `threshold_used` DECIMAL(4,2) NULL DEFAULT NULL,
    `available_capital` DECIMAL(18,2) NULL DEFAULT NULL,
    `total_trades` INT(11) NULL DEFAULT '0',
    `winning_trades` INT(11) NULL DEFAULT '0',
    `trades_blocked` INT(11) NULL DEFAULT '0',
    `last_check` TIMESTAMP NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    `last_signal_action` ENUM('BUY','SELL','HOLD','BLOCKED_BEAR','BLOCKED_LATERAL') NULL DEFAULT 'HOLD',
    PRIMARY KEY (`id`),
    UNIQUE INDEX `unique_user_pair_env` (`user_id`, `pair`, `environment`),
    INDEX `idx_user` (`user_id`),
    INDEX `idx_last_check` (`last_check`),
    INDEX `idx_bot_states_user_env` (`user_id`, `environment`),
    CONSTRAINT `bot_states_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB COLLATE='utf8mb4_unicode_ci';
```

**API Status:** ✅ Completamente implementado
- GET /api/bot/state/{pair}

**Notas:**
- Solo tiene `tp1_executed` y `tp2_executed` (no tp3)
- Usa `current_pnl_usd` y `current_pnl_percent` (no `pnl_usd`)
- `trades_blocked` en lugar de `blocked_trades`

---

### 3. trades ✅
```sql
CREATE TABLE `trades` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` INT(11) NOT NULL,
    `pair` VARCHAR(20) NOT NULL,
    `environment` ENUM('testnet','production') NOT NULL,
    `entry_price` DECIMAL(18,8) NOT NULL,
    `entry_time` TIMESTAMP NOT NULL,
    `entry_amount` DECIMAL(18,8) NOT NULL,
    `exit_price` DECIMAL(18,8) NULL DEFAULT NULL,
    `exit_time` TIMESTAMP NULL DEFAULT NULL,
    `exit_amount` DECIMAL(18,8) NULL DEFAULT NULL,
    `exit_reason` ENUM('TP1','TP2','TP3','STOP_LOSS','MANUAL','PARTIAL_TP1','PARTIAL_TP2') NULL DEFAULT NULL,
    `pnl_usd` DECIMAL(18,2) NULL DEFAULT NULL,
    `pnl_percent` DECIMAL(8,4) NULL DEFAULT NULL,
    `entry_regime` VARCHAR(20) NULL DEFAULT NULL,
    `entry_probability` DECIMAL(5,4) NULL DEFAULT NULL,
    `entry_volatility` DECIMAL(6,2) NULL DEFAULT NULL,
    `status` ENUM('OPEN','CLOSED') NULL DEFAULT 'OPEN',
    `created_at` TIMESTAMP NULL DEFAULT current_timestamp(),
    `updated_at` TIMESTAMP NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    PRIMARY KEY (`id`),
    INDEX `idx_user_pair` (`user_id`, `pair`),
    INDEX `idx_status` (`status`),
    INDEX `idx_entry_time` (`entry_time`),
    INDEX `idx_exit_time` (`exit_time`),
    INDEX `idx_trades_user_status_date` (`user_id`, `status`, `entry_time`),
    CONSTRAINT `trades_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB COLLATE='utf8mb4_unicode_ci';
```

**API Status:** ✅ Completamente implementado
- GET /api/bot/trades/recent/{pair}
- GET /api/bot/trades (paginated)
- GET /api/bot/performance

**Notas:**
- Usa `entry_amount` y `exit_amount` (no solo `amount`)
- Tiene campos de entrada: `entry_regime`, `entry_probability`, `entry_volatility`
- Soporta salidas parciales: `PARTIAL_TP1`, `PARTIAL_TP2`

---

### 4. bot_configurations ✅
```sql
CREATE TABLE `bot_configurations` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` INT(11) NOT NULL,
    `pair` VARCHAR(20) NOT NULL,
    `environment` ENUM('testnet','production') NOT NULL,
    `stop_loss_percent` DECIMAL(5,2) NULL DEFAULT '4.50',
    `position_size_percent` DECIMAL(5,2) NULL DEFAULT '50.00',
    `take_profit_1_percent` DECIMAL(5,2) NULL DEFAULT '5.00',
    `take_profit_2_percent` DECIMAL(5,2) NULL DEFAULT '7.50',
    `take_profit_3_percent` DECIMAL(5,2) NULL DEFAULT '10.00',
    `buy_threshold` DECIMAL(4,2) NULL DEFAULT '0.60',
    `regime_filter_enabled` TINYINT(1) NULL DEFAULT '1',
    `adaptive_threshold` TINYINT(1) NULL DEFAULT '1',
    `is_active` TINYINT(1) NULL DEFAULT '1',
    `created_at` TIMESTAMP NULL DEFAULT current_timestamp(),
    `updated_at` TIMESTAMP NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    PRIMARY KEY (`id`),
    UNIQUE INDEX `unique_user_pair_env` (`user_id`, `pair`, `environment`),
    INDEX `idx_user_pair` (`user_id`, `pair`),
    CONSTRAINT `bot_configurations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB COLLATE='utf8mb4_unicode_ci';
```

**API Status:** ✅ Completamente implementado
- GET /api/config/bot/{pair}/{environment}
- Created automatically when saving API keys

---

### 5. api_configurations ✅
```sql
CREATE TABLE `api_configurations` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` INT(11) NOT NULL,
    `environment` ENUM('testnet','production') NOT NULL,
    `api_key_encrypted` TEXT NOT NULL,
    `secret_key_encrypted` TEXT NOT NULL,
    `created_at` TIMESTAMP NULL DEFAULT current_timestamp(),
    `updated_at` TIMESTAMP NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    `is_active` TINYINT(1) NULL DEFAULT '1',
    PRIMARY KEY (`id`),
    UNIQUE INDEX `unique_user_environment` (`user_id`, `environment`),
    INDEX `idx_user` (`user_id`),
    CONSTRAINT `api_configurations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB COLLATE='utf8mb4_unicode_ci';
```

**API Status:** ✅ Completamente implementado
- GET /api/config/{environment}
- POST /api/config/save

**Notas:**
- API keys son encriptadas con AES-256
- Tiene campo `is_active` (no usado actualmente en la API)

---

### 6. docker_containers ✅
```sql
CREATE TABLE `docker_containers` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` INT(11) NOT NULL,
    `container_id` VARCHAR(100) NULL DEFAULT NULL,
    `environment` ENUM('testnet','production') NOT NULL,
    `status` ENUM('running','stopped','restarting','error') NULL DEFAULT 'stopped',
    `image_version` VARCHAR(50) NULL DEFAULT 'v4.0',
    `last_restart` TIMESTAMP NULL DEFAULT NULL,
    `created_at` TIMESTAMP NULL DEFAULT current_timestamp(),
    PRIMARY KEY (`id`),
    UNIQUE INDEX `unique_user_container` (`user_id`, `environment`),
    UNIQUE INDEX `container_id` (`container_id`),
    INDEX `idx_user` (`user_id`),
    INDEX `idx_status` (`status`),
    CONSTRAINT `docker_containers_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB COLLATE='utf8mb4_unicode_ci';
```

**API Status:** ✅ Completamente implementado
- GET /api/config/container/status/{environment}

**Notas:**
- Tiene `image_version` (no usado actualmente en la API)
- No tiene `updated_at`, solo `created_at`

---

## 📋 Tablas NO Implementadas (Futuras Features)

### 7. bot_logs ⏳
```sql
CREATE TABLE `bot_logs` (
    `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
    `user_id` INT(11) NOT NULL,
    `pair` VARCHAR(20) NOT NULL,
    `environment` ENUM('testnet','production') NOT NULL,
    `log_level` ENUM('INFO','WARNING','ERROR','DEBUG') NOT NULL,
    `message` TEXT NOT NULL,
    `details` LONGTEXT NULL DEFAULT NULL COLLATE 'utf8mb4_bin',
    `created_at` TIMESTAMP NULL DEFAULT current_timestamp(),
    PRIMARY KEY (`id`),
    INDEX `idx_user_pair` (`user_id`, `pair`),
    INDEX `idx_created` (`created_at`),
    INDEX `idx_level` (`log_level`),
    INDEX `idx_logs_user_date_level` (`user_id`, `created_at`, `log_level`),
    CONSTRAINT `bot_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `details` CHECK (json_valid(`details`))
) ENGINE=InnoDB COLLATE='utf8mb4_unicode_ci';
```

**API Status:** ❌ No implementado
**Endpoints Sugeridos:**
- GET /api/bot/logs/{pair}/{environment}?level=ERROR&limit=50
- GET /api/bot/logs/recent

---

### 8. partial_exits ⏳
```sql
CREATE TABLE `partial_exits` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `trade_id` INT(11) NOT NULL,
    `exit_type` ENUM('TP1','TP2') NOT NULL,
    `exit_price` DECIMAL(18,8) NOT NULL,
    `exit_amount` DECIMAL(18,8) NOT NULL,
    `exit_percent` DECIMAL(5,2) NOT NULL,
    `pnl_usd` DECIMAL(18,2) NOT NULL,
    `pnl_percent` DECIMAL(8,4) NOT NULL,
    `exit_time` TIMESTAMP NULL DEFAULT current_timestamp(),
    PRIMARY KEY (`id`),
    INDEX `idx_trade` (`trade_id`),
    CONSTRAINT `partial_exits_ibfk_1` FOREIGN KEY (`trade_id`) REFERENCES `trades` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB COLLATE='utf8mb4_unicode_ci';
```

**API Status:** ❌ No implementado
**Endpoints Sugeridos:**
- GET /api/bot/trades/{trade_id}/partial-exits

---

### 9. notifications ⏳
```sql
CREATE TABLE `notifications` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` INT(11) NOT NULL,
    `notification_type` ENUM('TRADE_OPEN','TRADE_CLOSE','TP_HIT','STOP_LOSS','ERROR','CONTAINER_RESTART') NOT NULL,
    `channel` ENUM('email','telegram','push') NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `message` TEXT NOT NULL,
    `sent_at` TIMESTAMP NULL DEFAULT current_timestamp(),
    `status` ENUM('pending','sent','failed') NULL DEFAULT 'pending',
    PRIMARY KEY (`id`),
    INDEX `idx_user` (`user_id`),
    INDEX `idx_status` (`status`),
    INDEX `idx_sent` (`sent_at`),
    CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB COLLATE='utf8mb4_unicode_ci';
```

**API Status:** ❌ No implementado
**Endpoints Sugeridos:**
- GET /api/notifications?status=pending
- POST /api/notifications/{id}/mark-read

---

### 10. user_notification_settings ⏳
```sql
CREATE TABLE `user_notification_settings` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` INT(11) NOT NULL,
    `email_enabled` TINYINT(1) NULL DEFAULT '1',
    `telegram_enabled` TINYINT(1) NULL DEFAULT '0',
    `telegram_chat_id` VARCHAR(100) NULL DEFAULT NULL,
    `notify_on_trade_open` TINYINT(1) NULL DEFAULT '1',
    `notify_on_trade_close` TINYINT(1) NULL DEFAULT '1',
    `notify_on_tp_hit` TINYINT(1) NULL DEFAULT '1',
    `notify_on_stop_loss` TINYINT(1) NULL DEFAULT '1',
    `notify_on_errors` TINYINT(1) NULL DEFAULT '1',
    PRIMARY KEY (`id`),
    UNIQUE INDEX `unique_user` (`user_id`),
    CONSTRAINT `user_notification_settings_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB COLLATE='utf8mb4_unicode_ci';
```

**API Status:** ❌ No implementado
**Endpoints Sugeridos:**
- GET /api/settings/notifications
- PUT /api/settings/notifications

---

## ✅ API Implementation Status

| Tabla | Status | Endpoints |
|-------|--------|-----------|
| users | ✅ 100% | 4/4 |
| bot_states | ✅ 100% | 1/1 |
| trades | ✅ 100% | 3/3 |
| bot_configurations | ✅ 100% | 1/1 |
| api_configurations | ✅ 100% | 2/2 |
| docker_containers | ✅ 100% | 1/1 |
| bot_logs | ❌ 0% | 0/2 |
| partial_exits | ❌ 0% | 0/1 |
| notifications | ❌ 0% | 0/2 |
| user_notification_settings | ❌ 0% | 0/2 |

**Total Implementado:** 6/10 tablas (60%)
**Total Endpoints:** 12/18 posibles

---

## 🔑 Key Differences from Original Assumptions

### bot_states
- ❌ No `tp3_executed`
- ✅ Uses `current_pnl_usd` instead of `pnl_usd`
- ✅ `trades_blocked` instead of `blocked_trades`
- ✅ Has `threshold_used` and `last_signal_action`

### trades
- ✅ Has `entry_amount` AND `exit_amount` (not just `amount`)
- ✅ Has entry context: `entry_regime`, `entry_probability`, `entry_volatility`
- ✅ Supports partial exits in `exit_reason`

### api_configurations
- ✅ Has `is_active` flag
- ✅ Has `updated_at`

### docker_containers
- ✅ Has `image_version`
- ❌ No `updated_at`

---

## 📝 Notes

1. **All tables use CASCADE deletion** - When a user is deleted, all related data is removed
2. **Most tables have updated_at** - Automatically updated on row modification
3. **ENUM fields** are heavily used for data validation at DB level
4. **Indexes are optimized** for common queries (user_id + pair, status, timestamps)
5. **Decimal precision** is consistent: DECIMAL(18,8) for prices, DECIMAL(18,2) for USD

---

**Last Updated:** 2026-01-09
**Database Version:** Production Schema v4.0
