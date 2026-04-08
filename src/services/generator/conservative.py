"""Conservative strategy: only fills unassigned slots, respects all constraints."""

from collections import defaultdict
from datetime import date

from .base import GenerationContext, GenerationStrategy, ProposedAssignment


class ConservativeStrategy(GenerationStrategy):
    def generate(self, ctx: GenerationContext) -> list[ProposedAssignment]:
        if not ctx.work_shifts or not ctx.members:
            return []

        assigned: set[tuple[int, date]] = set()
        member_hours: dict[int, float] = defaultdict(float)
        member_consecutive: dict[int, int] = defaultdict(int)
        member_last_work: dict[int, date | None] = {m.id: None for m in ctx.members}

        for ex in ctx.existing:
            assigned.add((ex.member_id, ex.date))
            st = ctx.all_shifts.get(ex.shift_type_id)
            if st and st.counts_as_work_time:
                member_hours[ex.member_id] += st.hours
                member_last_work[ex.member_id] = ex.date

        proposals: list[ProposedAssignment] = []
        total_days = len(ctx.dates)
        weeks = max(total_days / 7, 1)

        for d in ctx.dates:
            is_weekend = d.weekday() >= 5
            sorted_members = sorted(ctx.members, key=lambda m: member_hours[m.id])

            for member in sorted_members:
                key = (member.id, d)

                # ONLY fill unassigned slots
                if key in assigned:
                    continue

                # Skip weekends if not allowed
                if is_weekend and not ctx.allow_weekend_work:
                    if ctx.rest_shift_id:
                        proposals.append(ProposedAssignment(member.id, d, ctx.rest_shift_id))
                    continue

                # Check limit
                avg_weekly = member_hours[member.id] / weeks
                limit = min(ctx.weekly_hour_limit, member.weekly_hour_limit)
                if avg_weekly >= limit:
                    if ctx.rest_shift_id:
                        proposals.append(ProposedAssignment(member.id, d, ctx.rest_shift_id))
                    continue

                # Check consecutive days
                last = member_last_work.get(member.id)
                if last and (d - last).days == 1:
                    member_consecutive[member.id] += 1
                else:
                    member_consecutive[member.id] = 1

                if member_consecutive[member.id] >= ctx.max_consecutive_days:
                    if ctx.rest_shift_id:
                        proposals.append(ProposedAssignment(member.id, d, ctx.rest_shift_id))
                    member_consecutive[member.id] = 0
                    member_last_work[member.id] = None
                    continue

                shift_idx = hash((member.id, d.toordinal())) % len(ctx.work_shifts)
                shift = ctx.work_shifts[shift_idx]

                proposals.append(ProposedAssignment(member.id, d, shift.id))
                assigned.add(key)
                member_hours[member.id] += shift.hours
                member_last_work[member.id] = d

        return proposals
