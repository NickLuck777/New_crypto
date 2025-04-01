-- Table for reading data from Kafka
CREATE TABLE kafka_etherium (
    type UInt64 COMMENT 'Ethereum transaction type',
    chainId String COMMENT 'Network chain ID',
    nonce String COMMENT 'Transaction nonce',
    gas Int COMMENT 'Gas limit',
    maxFeePerGas Int COMMENT 'Maximum fee per gas',
    maxPriorityFeePerGas Int COMMENT 'Maximum priority fee per gas',
    "to" String COMMENT 'Recipient address',
    value Int COMMENT 'Transfer amount (in wei)',
    accessList String COMMENT 'Access list (for EIP-2930)',
    input String COMMENT 'Transaction data (for contract calls)',
    r String COMMENT 'ECDSA signature component',
    s String COMMENT 'ECDSA signature component',
    yParity Int COMMENT 'Y parity (for public key recovery)',
    v Int COMMENT 'ECDSA signature recovery parameter',
    hash String COMMENT 'Transaction hash',
    blockHash String COMMENT 'Hash of the block containing the transaction',
    blockNumber Int COMMENT 'Block number',
    transactionIndex Int COMMENT 'Transaction index within the block',
    "from" String COMMENT 'Sender address',
    gasPrice Int COMMENT 'Gas price (for legacy transactions)'
)
ENGINE = Kafka()
COMMENT 'Table for continuously reading raw Ethereum transaction data from the Kafka topic'
SETTINGS kafka_broker_list = '172.28.0.10:9092',
         kafka_topic_list = 'ethereum',
         kafka_group_name = 'group1',
         kafka_format = 'JSONEachRow';

-- Table for final information storage
CREATE TABLE etherium_transactions (
    timestamp DateTime COMMENT 'Time when the record was added to the ClickHouse table',
    type UInt64 COMMENT 'Ethereum transaction type',
    chainId String COMMENT 'Network chain ID',
    nonce String COMMENT 'Transaction nonce',
    gas Int COMMENT 'Gas limit',
    maxFeePerGas Int COMMENT 'Maximum fee per gas',
    maxPriorityFeePerGas Int COMMENT 'Maximum priority fee per gas',
    "to" String COMMENT 'Recipient address',
    value Int COMMENT 'Transfer amount (in wei)',
    accessList String COMMENT 'Access list (for EIP-2930)',
    input String COMMENT 'Transaction data (for contract calls)',
    r String COMMENT 'ECDSA signature component',
    s String COMMENT 'ECDSA signature component',
    yParity Int COMMENT 'Y parity (for public key recovery)',
    v Int COMMENT 'ECDSA signature recovery parameter',
    hash String COMMENT 'Transaction hash',
    blockHash String COMMENT 'Hash of the block containing the transaction',
    blockNumber Int COMMENT 'Block number',
    transactionIndex Int COMMENT 'Transaction index within the block',
    "from" String COMMENT 'Sender address',
    gasPrice Int COMMENT 'Gas price (for legacy transactions)'
)
ENGINE = MergeTree()
COMMENT 'Final table for storing processed Ethereum transactions'
ORDER BY (timestamp)
SETTINGS index_granularity = 8192;

-- Materialized View
-- This view automatically reads data from the kafka_etherium table,
-- adds the current timestamp (from the ClickHouse server), and inserts it
-- into the etherium_transactions table.
CREATE MATERIALIZED VIEW ethereum_consumer TO etherium_transactions 
AS 
SELECT  now() as timestamp, -- Use now() to get DateTime
    type,
    chainId,
    nonce,
    gas,
    maxFeePerGas,
    maxPriorityFeePerGas,
    "to",
    value,
    accessList,
    input,
    r,
    s,
    yParity,
    v,
    hash,
    blockHash,
    blockNumber,
    transactionIndex,
    "from",
    gasPrice
FROM kafka_etherium;