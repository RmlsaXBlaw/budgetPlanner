CREATE TABLE Household (
    Household_id INT NOT NULL AUTO_INCREMENT,
    Household_name VARCHAR(40) NOT NULL,
    PRIMARY KEY (Household_id)
);

CREATE TABLE Users (
    User_id INT NOT NULL AUTO_INCREMENT,
    Household_id INT NULL,
    User_status ENUM('member', 'admin') NULL,
    Username VARCHAR(50) NOT NULL,
    Pass VARCHAR(60) NOT NULL, -- 60 characters is the length of bcrypt hash
    PRIMARY KEY (User_id),
    FOREIGN KEY (Household_id) REFERENCES Household(Household_id),
    CHECK (
        (Household_id IS NULL AND User_status IS NULL)
        OR
        (Household_id IS NOT NULL AND User_status IS NOT NULL)
    )
);

CREATE TABLE Category (
    Category_id INT NOT NULL AUTO_INCREMENT,
    Household_id INT NULL,
    User_id INT NULL,
    Category_name VARCHAR(40) NOT NULL,
    Category_type ENUM('income', 'expenses') NOT NULL,
    PRIMARY KEY (Category_id),
    FOREIGN KEY (Household_id) REFERENCES Household(Household_id),
    FOREIGN KEY (User_id) REFERENCES Users(User_id),
    CHECK (
        (Household_id IS NOT NULL AND User_id IS NULL)
        OR
        (Household_id IS NULL AND User_id IS NOT NULL)
    )

);

CREATE TABLE Transactions (
    Transaction_id INT NOT NULL AUTO_INCREMENT,
    Household_id INT NULL,
    User_id INT NULL,
    Category_id INT NOT NULL,
    Amount DECIMAL(8,2) NOT NULL, 
    Transaction_date DATE NOT NULL, 
    Transaction_desc TEXT NULL,
    PRIMARY KEY (Transaction_id),
    FOREIGN KEY (Household_id) REFERENCES Household(Household_id),
    FOREIGN KEY (User_id) REFERENCES Users(User_id),
    FOREIGN KEY (Category_id) REFERENCES Category(Category_id),
    CHECK (
        (Household_id IS NOT NULL AND User_id IS NULL)
        OR
        (Household_id IS NULL AND User_id IS NOT NULL)
    )
);


CREATE TABLE Budget (
    Budget_id INT NOT NULL AUTO_INCREMENT,
    Household_id INT NULL,
    User_id INT NULL,
    Category_id INT NOT NULL,
    Budget_month TINYINT NOT NULL,
    Budget_year YEAR NOT NULL,
    Amount DECIMAL(8,2) NOT NULL,
    PRIMARY KEY (Budget_id),
    FOREIGN KEY (Household_id) REFERENCES Household(Household_id),
    FOREIGN KEY (User_id) REFERENCES Users(User_id),
    FOREIGN KEY (Category_id) REFERENCES Category(Category_id),
    CONSTRAINT UC_Budget UNIQUE (Household_id, User_id, Category_id, Budget_month, Budget_year),
    CHECK (
        (Household_id IS NOT NULL AND User_id IS NULL)
        OR
        (Household_id IS NULL AND User_id IS NOT NULL)
    )
);