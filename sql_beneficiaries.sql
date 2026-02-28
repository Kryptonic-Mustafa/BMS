
USE bank_app;

CREATE TABLE IF NOT EXISTS beneficiaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL, -- Who owns this contact
    saved_name VARCHAR(100), -- Nickname (e.g. "Dad", "Office")
    account_number VARCHAR(20) NOT NULL, -- The target account
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
