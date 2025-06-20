class BudgetManager:
    def __init__(self, budgets, threshold):
        """
        budgets: Dict[str, Dict[str, float]] -> {department: {category: budget}}
        threshold: float -> maximum overflow tolerance
        """
        self.budgets = budgets
        self.remaining = {dept: {cat: amt for cat, amt in cats.items()} for dept, cats in budgets.items()}
        self.threshold = threshold
        self.overflow_announced = False

    def approve_expense(self, department, category, amount):
        if self.overflow_announced:
            print("[ERROR] Budget exhausted and threshold already used. Expense denied.")
            return 0.0, "denied"

        remaining = self.remaining[department][category]

        if amount <= remaining:
            self.remaining[department][category] -= amount
            return amount, "full"

        overflow = amount - remaining

        if amount <= self.threshold:
            approved_amount = amount
            self.remaining[department][category] = 0
            if not self.overflow_announced:
                self.overflow_announced = True
                print("[WARNING] Threshold reached. Future expenses will be denied.")
            return approved_amount, "partial"

        if not self.overflow_announced:
            approved_amount = self.threshold
            self.overflow_announced = True
            self.remaining[department][category] = 0
            print("[WARNING] Threshold exceeded. Only threshold amount will be reimbursed.")
            return approved_amount, "partial"

    def get_remaining_budget(self, department=None):
        if department:
            return self.remaining.get(department, {})
        return self.remaining

