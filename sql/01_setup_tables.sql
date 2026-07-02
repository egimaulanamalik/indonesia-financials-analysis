-- companies
CREATE TABLE companies (
	ticker VARCHAR(10) PRIMARY KEY,
	company_name VARCHAR(100) NOT NULL,
	sector VARCHAR(50)
);

-- financial_statements
CREATE TABLE financial_statements (
	id SERIAL PRIMARY KEY,
	ticker VARCHAR(10) NOT NULL REFERENCES companies(ticker),
	statement_type VARCHAR(20) NOT NULL,
	line_item VARCHAR(150) NOT NULL,
	period DATE NOT NULL,
	value NUMERIC,
	CONSTRAINT uq_statement_row UNIQUE (ticker, statement_type, line_item, period)
);

-- core_metrics
CREATE TABLE core_metrics (
	line_item VARCHAR(150) PRIMARY KEY,
	metric_category VARCHAR(50) NOT NULL
); shoi