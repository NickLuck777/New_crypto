CREATE TABLE IF NOT EXISTS kafka_etherium (
    type Int32,
    "chainId" Nullable(Int64),
    nonce Nullable(Int64),
    gas Nullable(Int64),
    "maxFeePerGas" Nullable(Int64),
    "maxPriorityFeePerGas" Nullable(Int64),
    "to" Nullable(String),
    value Nullable(Int64),
    input Nullable(String),
    r Nullable(String),
    s Nullable(String),
    "yParity" Nullable(Int32),
    v Nullable(Int32),
    hash Nullable(String),
    "blockHash" Nullable(String),
    "blockNumber" Nullable(Int64),
    "transactionIndex" Nullable(Int64),
    "from" Nullable(String),
    "gasPrice" Nullable(Int64),
    "blobVersionedHashes" Array(String),
    "maxFeePerBlobGas" Nullable(Int64)
) ENGINE = Kafka()
SETTINGS kafka_broker_list = '172.28.0.10:9092',
         kafka_topic_list = 'ethereum_clickhouse',
         kafka_group_name = 'ethereum_trx',
         kafka_format = 'JSONEachRow', -- Исправляем формат
         kafka_skip_broken_messages = 1; -- Пропускаем битые сообщения


-- Создаём таблицу MergeTree
CREATE TABLE IF NOT EXISTS etherium_transactions (
    insertion_date DateTime DEFAULT now(),
    type Int32,
    "chainId" Nullable(Int64),
    nonce Nullable(Int64),
    gas Nullable(Int64),
    "maxFeePerGas" Nullable(Int64),
    "maxPriorityFeePerGas" Nullable(Int64),
    "to" Nullable(String),
    value Nullable(Int64),
    input Nullable(String),
    r Nullable(String),
    s Nullable(String),
    "yParity" Nullable(Int32),
    v Nullable(Int32),
    hash Nullable(String),
    "blockHash" Nullable(String),
    "blockNumber" Nullable(Int64),
    "transactionIndex" Nullable(Int64),
    "from" Nullable(String),
    "gasPrice" Nullable(Int64),
    "blobVersionedHashes" Array(String),
    "maxFeePerBlobGas" Nullable(Int64)
) ENGINE = MergeTree()
ORDER BY (insertion_date)
SETTINGS index_granularity = 8192;

-- Создаём материализованное представление
CREATE MATERIALIZED VIEW IF NOT EXISTS ethereum_consumer
TO etherium_transactions
AS
SELECT
    now() AS insertion_date,
    type,
    "chainId",
    nonce,
    gas,
    "maxFeePerGas",
    "maxPriorityFeePerGas",
    "to",
    value,
    input,
    r,
    s,
    "yParity",
    v,
    hash,
    "blockHash",
    "blockNumber",
    "transactionIndex",
    "from",
    "gasPrice",
    "blobVersionedHashes",
    "maxFeePerBlobGas"
FROM kafka_etherium;



drop table kafka_etherium;
drop table etherium_transactions;
drop table ethereum_consumer;

select * from ethereum_consumer;
select * from etherium_transactions;
select * from ethereum_consumer;

truncate table etherium_transactions;