CREATE TABLE eth_transactions (
    timestamp TIMESTAMP DEFAULT current_timestamp,
    type BIGINT NULL,
    "chainId" VARCHAR,
    nonce VARCHAR,
    gas INTEGER NULL,
    "maxFeePerGas" BIGINT NULL,          -- Allow NULL
    "maxPriorityFeePerGas" BIGINT NULL, -- Allow NULL
    "to" VARCHAR,
    value BIGINT NULL,
    input TEXT,
    r VARCHAR,
    s VARCHAR,
    "yParity" INTEGER NULL,
    v INTEGER,
    hash VARCHAR PRIMARY KEY,
    "blockHash" VARCHAR,
    "blockNumber" INTEGER NULL,
    "transactionIndex" INTEGER NULL,
    "from" VARCHAR,
    "gasPrice" BIGINT NULL                -- Allow NULL
);

COMMENT ON TABLE eth_transactions IS 'Table to store Ethereum transaction data retrieved from Kafka';

COMMENT ON COLUMN eth_transactions.timestamp IS 'Time when the record was inserted into the table (database time)';
COMMENT ON COLUMN eth_transactions.type IS 'Ethereum transaction type';
COMMENT ON COLUMN eth_transactions."chainId" IS 'Network chain ID';
COMMENT ON COLUMN eth_transactions.nonce IS 'Transaction nonce';
COMMENT ON COLUMN eth_transactions.gas IS 'Gas limit';
COMMENT ON COLUMN eth_transactions."maxFeePerGas" IS 'Maximum fee per gas (EIP-1559)';
COMMENT ON COLUMN eth_transactions."maxPriorityFeePerGas" IS 'Maximum priority fee per gas (EIP-1559)';
COMMENT ON COLUMN eth_transactions."to" IS 'Recipient address';
COMMENT ON COLUMN eth_transactions.value IS 'Transfer amount (in wei)';
COMMENT ON COLUMN eth_transactions.input IS 'Transaction data (for contract calls)';
COMMENT ON COLUMN eth_transactions.r IS 'ECDSA signature component';
COMMENT ON COLUMN eth_transactions.s IS 'ECDSA signature component';
COMMENT ON COLUMN eth_transactions."yParity" IS 'Y parity (for public key recovery)';
COMMENT ON COLUMN eth_transactions.v IS 'ECDSA signature recovery parameter';
COMMENT ON COLUMN eth_transactions.hash IS 'Transaction hash (Primary Key)';
COMMENT ON COLUMN eth_transactions."blockHash" IS 'Hash of the block containing the transaction';
COMMENT ON COLUMN eth_transactions."blockNumber" IS 'Block number';
COMMENT ON COLUMN eth_transactions."transactionIndex" IS 'Transaction index within the block';
COMMENT ON COLUMN eth_transactions."from" IS 'Sender address';
COMMENT ON COLUMN eth_transactions."gasPrice" IS 'Gas price (for legacy transactions)';

CREATE INDEX idx_timestamp ON eth_transactions (timestamp);