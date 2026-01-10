-- Migration: Add pair column to docker_containers table
-- This allows storing separate records for ETH and BTC containers

-- Step 1: Add pair column
ALTER TABLE docker_containers
ADD COLUMN pair VARCHAR(20) DEFAULT NULL AFTER container_id;

-- Step 2: Drop old unique constraint
ALTER TABLE docker_containers
DROP INDEX unique_user_container;

-- Step 3: Add new unique constraint including pair
ALTER TABLE docker_containers
ADD UNIQUE INDEX unique_user_environment_pair (user_id, environment, pair);

-- Step 4: Add index on pair for faster queries
ALTER TABLE docker_containers
ADD INDEX idx_pair (pair);

-- Step 5: Update existing records (if any) to set default pair
-- This is safe because we'll delete and recreate containers anyway
UPDATE docker_containers
SET pair = 'MULTI'
WHERE pair IS NULL;

-- Verification query
SELECT
    user_id,
    pair,
    environment,
    status,
    container_id,
    created_at
FROM docker_containers
ORDER BY created_at DESC;

-- Expected result: Now you can have multiple records like:
-- user_id=1, pair='ETHUSDT', environment='testnet'
-- user_id=1, pair='BTCUSDT', environment='testnet'
