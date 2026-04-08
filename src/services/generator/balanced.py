"""Balanced strategy: distributes shifts evenly across members, respecting constraints."""

from collections import defaultdict
from datetime import date, timedelta

from .base import GenerationContext, GenerationStrategy, ProposedAssignment


class BalancedStrategy(GenerationStrategy):
    def generate(self, ctx: GenerationContext) -> list[ProposedAssignment]:
        if not ctx.work_shifts or not ctx.members:
            return []

        # Track existing state
        assigned: dict[tuple[int, date], int] = {}  # (member_id, date) -> shift_type_id
        locked_cells: set[tuple[int, date]] = set()
        member_hours: dict[int, float] = defaultdict(float)
        member_consecutive: dict[int, int] = defaultdict(int)
        member_last_work: dict[int, date | None] = {m.id: None for m in ctx.members}

        for ex in ctx.existing:
            assigned[(ex.member_id, ex.date)] = ex.shift_type_id
            if ex.is_locked:
                locked_cells.add((ex.member_id, ex.date))
            # Count hours for work shifts
            if any(s.id == ex.shift_type_id and s.counts_as_work_time for s in ctx.work_shifts):
                member_hours[ex.member_id] += 8.0

        proposals: list[ProposedAssignment] = []
        total_days = len(ctx.dates)
        weeks = max(total_days / 7, 1)

        for d in ctx.dates:
            # Sort members by fewest hours (balance)
            sorted_members = sorted(ctx.members, key=lambda m: member_hours[m.id])

            for member in sorted_members:
                key = (member.id, d)

                # Skip if already assigned and fill_unassigned_only
                if ctx.fill_unassigned_only and key in assigned:
                    continue

                # Skip locked
                if key in locked_cells:
                    continue

                # Check weekly hour limit
                avg_weekly = member_hours[member.id] / weeks
                limit = min(ctx.weekly_hour_limit, member.weekly_hour_limit)
                if avg_weekly >= limit:
                    # Assign rest day if we have a rest shift
                    if ctx.rest_shift_id and key not in assigned:
                        proposals.append(ProposedAssignment(member.id, d, ctx.rest_shift_id))
                        assigned[key] = ctx.rest_shift_id
                    continue

                # Check consecutive days
                last = member_last_work.get(member.id)
                if last and (d - last).days == 1:
                    member_consecutive[member.id] += 1
                else:
                    member_consecutive[member.id] = 1

                if member_consecutive[member.id] >= ctx.max_consecutive_days:
                    if ctx.rest_shift_id and key not in assigned:
                        proposals.append(ProposedAssignment(member.id, d, ctx.rest_shift_id))
                        assigned[key] = ctx.rest_shift_id
                    member_consecutive[member.id] = 0
                    continue

                # Assign work shift (rotate through available shifts)
                shift_idx = hash((member.id, d.toordinal())) % len(ctx.work_shifts)
                shift = ctx.work_shifts[shift_idx]

                proposals.append(ProposedAssignment(member.id, d, shift.id))
                assigned[key] = shift.id
                member_hours[member.id] += 8.0
                member_last_work[member.id] = d

        return proposals
