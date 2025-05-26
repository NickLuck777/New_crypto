-- Create database if not exists
CREATE DATABASE IF NOT EXISTS blockchain_db;

-- Create table for storing Ethereum transactions
CREATE TABLE IF NOT EXISTS blockchain_db.etherium_transactions (
    timestamp timestamp,
    type Int32,
    "chainId" Int64,
    nonce Int64,
    gas Int64,
    "maxFeePerGas" Int64,
    "maxPriorityFeePerGas" Int64,
    "to" String,
    value Int64,
    input String,
    r String,
    s String,
    "yParity" Int32,
    v Int32,
    hash String,
    "blockHash" String,
    "blockNumber" Int64,
    "transactionIndex" Int64,
    "from" String,
    "gasPrice" Int64,
    "blobVersionedHashes" Array(String),
    "maxFeePerBlobGas" Int64
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (timestamp)
SETTINGS index_granularity = 8192;

-- Create table for storing sum of all values
CREATE TABLE IF NOT EXISTS blockchain_db.sum_all_values_tbl
(date date,
 gas Int64,
 "maxFeePerGas" Int64,
 "maxPriorityFeePerGas" Int64,
 value Int64,
 "gasPrice" Int64)
engine SummingMergeTree() 
partition by date
order by (date)
SETTINGS index_granularity = 8192;

-- Create materialized view for sum of all values
create materialized view blockchain_db.sum_all_values_mv
to blockchain_db.sum_all_values_tbl
as
select toDate(timestamp) as date,
	   gas,
	   "maxFeePerGas",
	   "maxPriorityFeePerGas",
	   value,
	   "gasPrice"
  from blockchain_db.etherium_transactions;

-- Create table for storing aggregated values for each sender
CREATE TABLE IF NOT EXISTS blockchain_db.agg_sender_values_tbl
(date date,
 sender String,
 trx_count AggregateFunction(count),
 gas AggregateFunction(sum, Int64),
 "maxFeePerGas" AggregateFunction(sum, Int64),
 "maxPriorityFeePerGas" AggregateFunction(sum, Int64),
 value AggregateFunction(sum, Int64),
 "gasPrice" AggregateFunction(sum, Int64))
engine AggregatingMergeTree() 
partition by (date)
order by (date, sender)
SETTINGS index_granularity = 8192;

-- Create materialized view for aggregated values for each sender
create materialized view blockchain_db.agg_sender_values_mv
to blockchain_db.agg_sender_values_tbl
as
select toDate(timestamp) as date,
	   "from" as sender,
	   countState() as trx_count,
	   sumState(ifNull(gas, 0)) AS gas,
       sumState(ifNull("maxFeePerGas", 0)) AS "maxFeePerGas",
       sumState(ifNull("maxPriorityFeePerGas", 0)) AS "maxPriorityFeePerGas",
       sumState(ifNull(value, 0)) AS value,
       sumState(ifNull("gasPrice", 0)) AS "gasPrice"
  from blockchain_db.etherium_transactions
group by date, sender;

-- Create table for storing news data
CREATE TABLE IF NOT EXISTS blockchain_db.crypto_news (
                          id String,
                          title String,
                          published String,
                          sentiment Float32,
                          insertion_date timestamp
                          ) ENGINE = MergeTree()
                          ORDER BY (published, id);