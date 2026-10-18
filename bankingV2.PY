# the aim of this project is to rebuild the bank prj using OOP style

from random import randint
import re
from tempfile import template
from datetime import datetime
from database import get_connection
from decimal import Decimal


class Account:
    def __init__(self, full_name, phone_number, email, account_number, balance, pin, history, id = None):
        self.id = id
        self.full_name = full_name
        self.phone_number = phone_number
        self.email = email
        self.account_number = account_number
        self.balance = balance
        self.pin = pin
        self.history = history

    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            self.history.append(f"Deposited ${amount} at {time()}")
            print("Deposit Succesful!")
            print(f"your new balance is {self.balance}")
        else:
            print("invalid input")

    def withdraw(self, amount, pin):
        if amount > self.balance:
            print("insufficient balance!")
            return
        
        elif self.pin != pin:
            return "incorrect password"
        
        else:
            self.balance -= amount
            print("withdrawal succesful!")
            self.history.append(f"Withdrew ${amount} at {time()}")

    def check_balance(self):
        print(f"your balance: {self.balance}")

    def view_account_information(self):
        print("full name: ", self.full_name)
        print("account Num ber: ", self.account_number)
        print("phone_number: ", self.phone_number)
        print("email: ", self.email)
        print("")

    def transaction_history(self,cursor):
        cursor.execute("""SELECT transaction_type, amount, receiver_name, time
        FROM history
        WHERE account_id = %s
        ORDER BY time""",(self.id,))

        for transaction_type, amount,receiver, t in cursor.fetchall():
            to = f" to {receiver}" if receiver else""
            print(f"{transaction_type} ${amount} {to} at {t}")


class Bank:
    def __init__(self):
        self.accounts = []

        self.connection = get_connection()
        self.cursor = self.connection.cursor()

        self.connection.commit()
        self.load_account()

    def create_account(self, full_name, phone_number, email,  pin, balance, history,):
        account_number = str(randint(1000000000, 9999999999))

        new_account = Account(
            full_name=full_name,
            phone_number=phone_number,
            email=email,
            account_number=account_number,
            balance=balance,
            pin=pin,
            history=history)

        self.accounts.append(new_account)

        self.save_account(new_account)

        return new_account

    def find_account(self, account_number):
        for account in self.accounts:
            if account.account_number == account_number:
                return account

    def login(self):
        account_number = input("enter your account number: ").strip()
        pin = input("enter your account password: ").strip()

        for account in self.accounts:

            if account_number == account.account_number:

                if pin == account.pin:
                    print("login successful!")
                    self.bank_menu(account)
                    return

                else:
                    print("incorrect Pin")
                    return

        print("account not found!")
        return

    def bank_menu(self, account):

        while True:

            print("welcome to Max bank")
            print("")
            print(f"your account balance: {account.balance}")
            print("")
            print("1. Deposit")
            print("2. Withdraw")
            print("3. Transfer")
            print("4. View account Info")
            print("5. check Transaction History")
            print("6. Logout")

            option = input("enter your option: ")

            if option == "1":
                amount = Decimal(input("enter deposit amount: "))
                account.deposit(amount)
     
                self.cursor.execute(""" UPDATE accounts SET balance = %s 
                WHERE account_number = %s """,
                (account.balance, account.account_number))

                self.cursor.execute(""" INSERT INTO history
                (account_id, account_number, transaction_type, amount, receiver_name, time)
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (account.id, account.account_number, "Deposit", amount, None, time()))

                self.connection.commit()

            elif option == "2":
                amount = Decimal(input("enter withdraw amount: "))

                if amount > account.balance:
                    print("Insufficient balance!")

                else:
                    pin = input("enter your password: ")
                    account.withdraw(amount, pin)

                    self.cursor.execute(""" UPDATE accounts SET balance = %s 
                    WHERE account_number =%s """,
                    (account.balance, account.account_number))

                    self.cursor.execute(""" INSERT INTO history
                    (account_id, account_number, transaction_type, amount, receiver_name, time)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (account.id, account.account_number, "Withdrawal", amount, None, time()))

                    self.connection.commit()


            elif option == "3":
                receiver_account = input(
                    "Enter receiver account number: ").strip()
                receiver = self.find_account(receiver_account)

                if receiver is None:
                    print("Receiver account not found.")
                    continue

                if receiver == account:
                    print("You can't transfer to yourself.")
                    continue

                amount = Decimal(input("Enter transfer amount: "))
                pin = input("Enter your PIN: ")

                self.transfer(account, receiver, amount, pin)
                

            elif option == "4":
                account.view_account_information()

            elif option == "5":
                account.transaction_history(self.cursor)

            elif option == "6":
                print("thank you for banking with us!")
                return

            else:
                print("Invalid input! enter a number 1-6")

    def transfer(self, sender, receiver, amount, pin):
        if receiver not in self.accounts:
            print("Receiver account not found.")
            return

        if receiver == sender:
            print("You can't transfer to yourself.")
            return

        if sender.pin != pin:
            print("Incorrect PIN.")
            return

        if amount <= 0:
            print("Transfer amount must be greater than zero.")
            return

        if amount > sender.balance:
            print("Insufficient balance.")
            return

        sender.balance -= amount
        receiver.balance += amount

        self.cursor.execute(""" UPDATE accounts SET balance = %s 
        WHERE account_number = %s """,
        (sender.balance, sender.account_number))

        self.cursor.execute(""" UPDATE accounts SET balance = %s 
        WHERE account_number = %s """,
        (receiver.balance, receiver.account_number))

        self.cursor.execute(""" INSERT INTO history
        (account_id, account_number, transaction_type, amount, receiver_name, time)
        VALUES (%s, %s, %s, %s, %s, %s)""",
        (sender.id, sender.account_number, "Transfer", amount, receiver.full_name, time()))

        self.cursor.execute(""" INSERT INTO history
        (account_id, account_number, transaction_type, amount, receiver_name, time)
        VALUES (%s, %s, %s, %s, %s, %s)""",
        (sender.id, receiver.account_number, "Received", amount, receiver.full_name, time()))

        self.connection.commit()
        
        sender.history.append(
            f"Transfered ${amount} to {receiver.full_name} at {time()}")
        receiver.history.append(
            f"Received ${amount} from {sender.full_name} at {time()}")

        print("Transaction successful!")

    def save_account(self, account):
        self.cursor.execute(""" 
        INSERT INTO accounts (full_name, phone_number, email, Account_number, Balance, pin)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""", 
            (account.full_name,
             account.phone_number,
             account.email,
             account.account_number,
             account.balance,
             account.pin))

        account.id = self.cursor.fetchone()[0]
        self.connection.commit() 

    def load_account(self):
        self.cursor.execute("""SELECT full_name, phone_number, email, account_number, balance,
                            pin, id
                            FROM accounts""")
        accounts_data = self.cursor.fetchall()

        for account_data in accounts_data:
            new_account = Account(account_data[0],
                                  account_data[1],
                                  account_data[2],
                                  account_data[3],
                                  account_data[4],
                                  account_data[5],
                                  [],
                                  id = account_data[6])
            
            self.accounts.append(new_account)
            
bank = Bank()          # object bank
bank.load_account()


def time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_account_user_inputs():

    while True:

        first_name = input("enter first name: ")
        if not first_name.strip():
            print("name can't be left empty/space")
            continue
        last_name = input("enter your last name: ")
        if not last_name.strip():
            print("names can't be left empty/space")
            continue
        break

    full_name = f"{first_name} {last_name}"

    while True:
        phone_number = input("enter your phone number: ")
        if len(str(phone_number)) != 11:
            print("phone number must be 11 digits")
            continue

        elif not str(phone_number).isdigit():
            print("phone number must be digits only")
            continue

        else:
            break

    while True:
        email_template = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        email = input("enter a valid email: ")

        if not re.match(email_template, email):
            print("invalid email! please enter a valid email")
        else:
            print("email accepted")
            break

    while True:
        pin = input("create a 6 digit pin: ").strip()
        if len(pin) != 6 or not pin.isdigit():
            print("pin must be 6 digits")
        else:
            print("password succesfully created")
            break

    balance = 0
    history = []
    new_account = bank.create_account(full_name, phone_number, email, pin, balance, history)

    print("Account created successfully!")
    print(f"Your account number is: {new_account.account_number}")

    return


while True:
    print("\n====== BANK APP ======")
    print("1. Create account")
    print("2. Login")
    print("3. Exit")

    option = input("Select an option (1-3): ").strip()

    if option == "1":
        create_account_user_inputs()

    elif option == "2":
        bank.login()

    elif option == "3":
        print("Thank you for banking with us.")
        break

    else:
        print("Invalid option. Please select 1, 2, or 3.")
