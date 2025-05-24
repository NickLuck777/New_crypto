-- Create table for storing Ethereum transactions
CREATE TABLE IF NOT EXISTS eth_transactions (
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    type INTEGER NULL,
    "chainId" VARCHAR,
    nonce VARCHAR,
    gas INTEGER NULL,
    "maxFeePerGas" BIGINT NULL,
    "maxPriorityFeePerGas" BIGINT NULL,
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
    "gasPrice" BIGINT NULL,
    "blobVersionedHashes" VARCHAR[] NULL,
    "maxFeePerBlobGas" BIGINT NULL
);

-- Add comments for documentation
COMMENT ON TABLE eth_transactions IS 'Table to store Ethereum transaction data retrieved from Kafka';
COMMENT ON COLUMN eth_transactions.timestamp IS 'Time when the record was inserted into the table (UTC)';
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
COMMENT ON COLUMN eth_transactions."blobVersionedHashes" IS 'Array of blob versioned hashes (EIP-4844)';
COMMENT ON COLUMN eth_transactions."maxFeePerBlobGas" IS 'Maximum fee per blob gas (EIP-4844)';

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_timestamp ON eth_transactions (timestamp);

-- Create table for storing crypto news
CREATE TABLE IF NOT EXISTS crypto_news (
    id varchar,
    title varchar,
    published varchar,
    sentiment Float,
    insertion_date timestamp default now()
);

-- Add comments for documentation
COMMENT ON TABLE crypto_news IS 'Table to store processed crypto-related news with sentiment score.';

COMMENT ON COLUMN crypto_news.id IS 'Unique identifier of the news item.';
COMMENT ON COLUMN crypto_news.title IS 'Title or headline of the news article.';
COMMENT ON COLUMN crypto_news.published IS 'Original publication timestamp of the article (as string).';
COMMENT ON COLUMN crypto_news.sentiment IS 'Sentiment score of the article (e.g., -1 to 1).';
COMMENT ON COLUMN crypto_news.insertion_date IS 'Timestamp when the record was inserted into the table (UTC).';
