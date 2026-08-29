"""CP-SAT model kurulumu: karar değişkenleri ve yardımcı ifadeler."""

from ortools.sat.python import cp_model

from .types import SolveRequest


class ModelVars:
    def __init__(self, model: cp_model.CpModel, request: SolveRequest) -> None:
        self.dates = request.dates()
        self.shift_types = request.profile.shift_types

        # x[nurse_id, day, shift_code] ∈ {0, 1}
        self.x: dict[tuple[str, object, str], cp_model.IntVar] = {}
        for nurse in request.nurses:
            for day in self.dates:
                for shift in self.shift_types:
                    self.x[(nurse.id, day, shift.code)] = model.NewBoolVar(
                        f"x_{nurse.id}_{day.isoformat()}_{shift.code}"
                    )

        # worked[nurse_id, day] = O gün herhangi bir vardiyaya atanmış mı (H4, S2 için)
        self.worked: dict[tuple[str, object], cp_model.IntVar] = {}
        for nurse in request.nurses:
            for day in self.dates:
                var = model.NewBoolVar(f"worked_{nurse.id}_{day.isoformat()}")
                model.AddMaxEquality(var, [self.x[(nurse.id, day, shift.code)] for shift in self.shift_types])
                self.worked[(nurse.id, day)] = var


def build(request: SolveRequest) -> tuple[cp_model.CpModel, ModelVars]:
    model = cp_model.CpModel()
    mv = ModelVars(model, request)
    return model, mv
