import uuid

class Calisan:
    def __init__(self, isim, departman, employee_id=None):
        self.isim = isim
        self.departman = departman
        self.employee_id = employee_id if employee_id is not None else str(uuid.uuid4())

    def __repr__(self):
        return f"Calisan(employee_id='{self.employee_id}', isim='{self.isim}', departman='{self.departman}')"

