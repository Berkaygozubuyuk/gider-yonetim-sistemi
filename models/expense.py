from datetime import datetime

class Expense:
    def __init__(self, employee, amount, category, date):
        self.employee = employee
        self.amount = amount
        self.category = category
        self.date = date
        self.approved = False
        self.reimbursed = False
        self.reimbursed_amount = 0.0

    def __repr__(self):
        return f"Expense(employee={self.employee.name}, amount={self.amount}, category={self.category}, date={self.date}, approved={self.approved}, reimbursed={self.reimbursed})"

