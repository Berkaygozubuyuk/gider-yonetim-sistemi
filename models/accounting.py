from models.expense import Expense
from models.budget import BudgetManager

class Accounting:
    def __init__(self, budget_mgr: BudgetManager):
        self.budget_mgr = budget_mgr

    def reimburse(self, expense):
        if expense.approved and not expense.reimbursed:
            reimbursed_amt, status = self.budget_mgr.approve_expense(
                expense.employee.department, expense.category, expense.amount
            )
            expense.reimbursed_amount = reimbursed_amt
            if status != "denied":
                expense.reimbursed = True

