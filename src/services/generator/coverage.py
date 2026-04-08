"""Coverage strategy: prioritizes filling all slots, respects constraints."""

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
            st = ctx.all_shifts.get(ex.shift_type_id)
            if st and st.counts_as_work_time:
                member_hours[ex.member_id] += st.hours

        proposals: list[ProposedAssignment] = []
        total_days = len(ctx.dates)
        weeks = max(total_days / 7, 1)

        for d in ctx.dates:
            is_weekend = d.weekday() >= 5

            for member in ctx.members:
                key = (member.id, d)

                if ctx.fill_unassigned_only and key in assigned:
                    continue
                if key in locked_cells:
                    continue

                # Skip weekends if not allowed
                if is_weekend and not ctx.allow_weekend_work:
                    if ctx.rest_shift_id and key not in assigned:
                        proposals.append(ProposedAssignment(member.id, d, ctx.rest_shift_id))
                        assigned[key] = ctx.rest_shift_id
                    continue

                # Check limit (softer for coverage — allow up to 110%)
                avg_weekly = member_hours[member.id] / weeks
                limit = min(ctx.weekly_hour_limit, member.weekly_hour_limit)
                if avg_weekly >= limit * 1.1:
                    if ctx.rest_shift_id and key not in assigned:
                        proposals.append(ProposedAssignment(member.id, d, ctx.rest_shift_id))
                        assigned[key] = ctx.rest_shift_id
                    continue

                # Pick shift with least coverage that day
                shift_counts: dict[int, int] = defaultdict(int)
                for m in ctx.members:
                    existing_shift = assigned.get((m.id, d))
                    if existing_shift:
                        shift_counts[existing_shift] += 1

                best_shift = min(ctx.work_shifts, key=lambda s: shift_counts.get(s.id, 0))

                proposals.append(ProposedAssignment(member.id, d, best_shift.id))
                assigned[key] = best_shift.id
                member_hours[member.id] += best_shift.hours

        return proposals
