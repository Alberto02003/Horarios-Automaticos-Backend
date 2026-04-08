"""Coverage strategy: prioritizes filling all slots, may exceed balance."""

from collections import defaultdict
from datetime import date

from .base import GenerationContext, GenerationStrategy, ProposedAssignment


class CoverageStrategy(GenerationStrategy):
    def generate(self, ctx: GenerationContext) -> list[ProposedAssignment]:
        if not ctx.work_shifts or not ctx.members:
            return []

        assigned: dict[tuple[int, date], int] = {}
        locked_cells: set[tuple[int, date]] = set()
        member_hours: dict[int, float] = defaultdict(float)

        for ex in ctx.existing:
            assigned[(ex.member_id, ex.date)] = ex.shift_type_id
            if ex.is_locked:
                locked_cells.add((ex.member_id, ex.date))
            if any(s.id == ex.shift_type_id and s.counts_as_work_time for s in ctx.work_shifts):
                member_hours[ex.member_id] += 8.0

        proposals: list[ProposedAssignment] = []

        # For each date, ensure every member has an assignment
        for d in ctx.dates:
            for member in ctx.members:
                key = (member.id, d)

                if ctx.fill_unassigned_only and key in assigned:
                    continue
                if key in locked_cells:
                    continue

                # Pick shift with least coverage that day
                shift_counts: dict[int, int] = defaultdict(int)
                for m in ctx.members:
                    existing_shift = assigned.get((m.id, d))
                    if existing_shift:
                        shift_counts[existing_shift] += 1

                # Find least-used work shift
                best_shift = min(ctx.work_shifts, key=lambda s: shift_counts.get(s.id, 0))

                proposals.append(ProposedAssignment(member.id, d, best_shift.id))
                assigned[key] = best_shift.id
                member_hours[member.id] += 8.0

        return proposals
