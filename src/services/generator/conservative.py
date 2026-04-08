"""Conservative strategy: only fills unassigned slots, makes minimal changes."""

from collections import defaultdict
from datetime import date

from .base import GenerationContext, GenerationStrategy, ProposedAssignment


class ConservativeStrategy(GenerationStrategy):
    def generate(self, ctx: GenerationContext) -> list[ProposedAssignment]:
        if not ctx.work_shifts or not ctx.members:
            return []

        assigned: set[tuple[int, date]] = set()
        member_hours: dict[int, float] = defaultdict(float)

        for ex in ctx.existing:
            assigned.add((ex.member_id, ex.date))
            if any(s.id == ex.shift_type_id and s.counts_as_work_time for s in ctx.work_shifts):
                member_hours[ex.member_id] += 8.0

        proposals: list[ProposedAssignment] = []
        total_days = len(ctx.dates)
        weeks = max(total_days / 7, 1)

        for d in ctx.dates:
            # Only fill gaps — sort by fewest hours
            sorted_members = sorted(ctx.members, key=lambda m: member_hours[m.id])

            for member in sorted_members:
                key = (member.id, d)

                # ONLY fill unassigned slots
                if key in assigned:
                    continue

                # Check limit
                avg_weekly = member_hours[member.id] / weeks
                limit = min(ctx.weekly_hour_limit, member.weekly_hour_limit)
                if avg_weekly >= limit:
                    if ctx.rest_shift_id:
                        proposals.append(ProposedAssignment(member.id, d, ctx.rest_shift_id))
                    continue

                # Simple round-robin shift selection
                shift_idx = hash((member.id, d.toordinal())) % len(ctx.work_shifts)
                shift = ctx.work_shifts[shift_idx]

                proposals.append(ProposedAssignment(member.id, d, shift.id))
                assigned.add(key)
                member_hours[member.id] += 8.0

        return proposals
