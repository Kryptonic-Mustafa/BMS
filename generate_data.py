import random

# Realistic Data Arrays
first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

sql_statements = ["USE bank_app;"]

print("Generating SQL for 50 Users...")

# We assume IDs start from 100 to avoid conflict with existing users
start_id = 100 

for i in range(50):
    user_id = start_id + i
    fname = random.choice(first_names)
    lname = random.choice(last_names)
    name = f"{fname} {lname}"
    email = f"{fname.lower()}.{lname.lower()}{random.randint(1,999)}@example.com"
    # Password hash for 'password123'
    password_hash = "$2a$10$x.pb.q/1.k1.g1.n1.o1.u1" 
    
    # 1. Insert User
    sql_statements.append(
        f"INSERT INTO users (id, name, email, password, role) VALUES ({user_id}, '{name}', '{email}', '{password_hash}', 'customer');"
    )

    # 2. Insert Account
    account_num = f"ACC{random.randint(1000000000, 9999999999)}"
    balance = round(random.uniform(500.00, 50000.00), 2)
    
    sql_statements.append(
        f"INSERT INTO accounts (user_id, account_number, balance, type, status) VALUES ({user_id}, '{account_num}', {balance}, 'savings', 'active');"
    )

# Write to file
with open("seed_customers.sql", "w") as f:
    f.write("\n".join(sql_statements))

print("✅ 'seed_customers.sql' created!")
print("👉 Open MySQL Workbench -> File -> Open SQL Script -> Select 'seed_customers.sql' -> Run (Lightning Bolt)")