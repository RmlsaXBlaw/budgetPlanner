/*
  NoSQL Document Database Structure (MongoDB)
  This replaces the relational database.sql configuration.
*/

// 1. USERS Collection
const userDocument = {
  _id: ObjectId("..."),
  username: "J.SMITH",
  password: "hashed_password",
  household_id: ObjectId("..."), // Nullable
  user_status: "admin" // Nullable, 'admin' or 'member'
};

// 2. HOUSEHOLDS Collection
const householdDocument = {
  _id: ObjectId("..."),
  name: "Smith Family"
};

// 3. CATEGORIES Collection
const categoryDocument = {
  _id: ObjectId("..."),
  owner_type: "user", // or 'household'
  owner_id: ObjectId("..."), 
  name: "Groceries",
  type: "expenses" // or 'income'
};

// 4. LEDGERS Collection (The core aggregate replacement for Budget & Transactions)
// Implements the "Bucket Pattern" to heavily optimize dashboard rendering.
const ledgerDocument = {
  _id: ObjectId("..."),
  owner_type: "user", // or 'household'
  owner_id: ObjectId("..."),
  month: 10,
  year: 2023,
  budgets: [
    { category_id: ObjectId("..."), amount: 500.00 }
  ],
  transactions: [
    {
      transaction_id: ObjectId("..."), // Unique identifier within array
      user_id: ObjectId("..."), // The user who made the transaction
      category_id: ObjectId("..."),
      amount: 45.00,
      date: ISODate("2023-10-15T00:00:00Z"),
      description: "Walmart groceries"
    }
  ]
};