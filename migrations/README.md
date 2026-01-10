# 🗄️ Database Migrations

Este directorio contiene migraciones SQL para actualizar el schema de la base de datos.

## 📋 Migraciones Disponibles

### 001 - Add pair to docker_containers ✅ **REQUERIDO**

**Archivo:** `001_add_pair_to_docker_containers.sql`

**Propósito:** Permitir almacenar 2 registros separados (ETH y BTC) en la tabla `docker_containers`.

**Cambios:**
- Agrega columna `pair VARCHAR(20)`
- Modifica UNIQUE constraint de `(user_id, environment)` a `(user_id, environment, pair)`
- Agrega índice en `pair`

**¿Por qué es necesario?**

Antes de esta migración:
- ❌ Solo se podía guardar 1 registro por user_id + environment
- ❌ El segundo contenedor (ETH o BTC) sobreescribía el primero

Después de esta migración:
- ✅ Se pueden guardar 2 registros: uno para ETHUSDT y otro para BTCUSDT
- ✅ Cada contenedor tiene su propio registro en la tabla

## 🚀 Cómo Ejecutar la Migración

### Opción 1: MySQL Command Line

```bash
# Conectar a MySQL
mysql -h YOUR_DB_HOST -u YOUR_DB_USER -p

# Seleccionar la base de datos
USE trading_bot_db;

# Ejecutar la migración
source /home/user/api_bot_trading_ia/migrations/001_add_pair_to_docker_containers.sql;

# Verificar los cambios
DESCRIBE docker_containers;
```

### Opción 2: Archivo SQL Directo

```bash
mysql -h YOUR_DB_HOST -u YOUR_DB_USER -p trading_bot_db < /home/user/api_bot_trading_ia/migrations/001_add_pair_to_docker_containers.sql
```

### Opción 3: Cliente GUI (MySQL Workbench, phpMyAdmin, DBeaver)

1. Abre el archivo `001_add_pair_to_docker_containers.sql`
2. Copia todo el contenido
3. Ejecuta en tu cliente SQL preferido

## ✅ Verificación

Después de ejecutar la migración, verifica que funcionó correctamente:

```sql
-- Ver la estructura de la tabla
DESCRIBE docker_containers;

-- Deberías ver:
-- | Field         | Type                                      | Null | Key | Default | Extra          |
-- | id            | int(11)                                   | NO   | PRI | NULL    | auto_increment |
-- | user_id       | int(11)                                   | NO   | MUL | NULL    |                |
-- | pair          | varchar(20)                               | YES  | MUL | NULL    |                | ← NUEVO
-- | container_id  | varchar(100)                              | YES  | UNI | NULL    |                |
-- | environment   | enum('testnet','production')             | NO   |     | NULL    |                |
-- | status        | enum('running','stopped','restarting'...) | YES  | MUL | stopped |                |
-- | image_version | varchar(50)                               | YES  |     | v4.0    |                |
-- | last_restart  | timestamp                                 | YES  |     | NULL    |                |
-- | created_at    | timestamp                                 | YES  |     | CURRENT_TIMESTAMP |      |

-- Ver los índices
SHOW INDEXES FROM docker_containers;

-- Deberías ver el nuevo UNIQUE constraint:
-- unique_user_environment_pair (user_id, environment, pair)
```

## 📊 Impacto en la Aplicación

### Antes de la Migración

Cuando guardas API keys:
```
POST /api/config/save → Crea 2 contenedores
├── Contenedor ETH creado ✅
├── Guarda en DB: user_id=1, environment=testnet ✅
├── Contenedor BTC creado ✅
└── Actualiza registro: user_id=1, environment=testnet ⚠️ (sobrescribe ETH)

Resultado en DB:
| user_id | pair | environment | container_id      |
|---------|------|-------------|-------------------|
| 1       | NULL | testnet     | MULTI:BTC:abc123  | ← Solo 1 registro
```

### Después de la Migración

Cuando guardas API keys:
```
POST /api/config/save → Crea 2 contenedores
├── Contenedor ETH creado ✅
├── Guarda en DB: user_id=1, pair=ETHUSDT, environment=testnet ✅
├── Contenedor BTC creado ✅
└── Guarda en DB: user_id=1, pair=BTCUSDT, environment=testnet ✅

Resultado en DB:
| user_id | pair    | environment | container_id |
|---------|---------|-------------|--------------|
| 1       | ETHUSDT | testnet     | abc123...    | ← Registro ETH
| 1       | BTCUSDT | testnet     | def456...    | ← Registro BTC
```

## ⚠️ Notas Importantes

1. **Backup:** Siempre haz backup de la base de datos antes de ejecutar migraciones:
   ```bash
   mysqldump -h YOUR_DB_HOST -u YOUR_DB_USER -p trading_bot_db > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Registros Existentes:** La migración actualiza registros existentes con `pair='MULTI'`. Estos serán reemplazados cuando recrees los contenedores.

3. **Orden:** Las migraciones deben ejecutarse en orden numérico (001, 002, etc.).

4. **Rollback:** Si necesitas revertir la migración:
   ```sql
   -- Revertir migración 001
   ALTER TABLE docker_containers DROP INDEX unique_user_environment_pair;
   ALTER TABLE docker_containers DROP INDEX idx_pair;
   ALTER TABLE docker_containers DROP COLUMN pair;
   ALTER TABLE docker_containers ADD UNIQUE INDEX unique_user_container (user_id, environment);
   ```

## 🔄 Estado de Migraciones

| # | Nombre | Estado | Fecha Ejecutada | Notas |
|---|--------|--------|-----------------|-------|
| 001 | add_pair_to_docker_containers | ⏳ Pendiente | - | **Requerido para v1.1** |

---

## 📝 Template para Nuevas Migraciones

Al crear una nueva migración, usa este formato:

```
migrations/
└── XXX_descriptive_name.sql
```

Donde:
- `XXX` = número secuencial (002, 003, etc.)
- `descriptive_name` = descripción breve del cambio

Contenido del archivo:
```sql
-- Migration XXX: Descriptive Title
-- Description: What this migration does and why

-- Your SQL commands here

-- Verification query
-- Add a SELECT to verify the migration worked
```

---

**Última Actualización:** 2026-01-10
**Versión de la Base de Datos:** v4.0 → v4.1 (después de 001)
