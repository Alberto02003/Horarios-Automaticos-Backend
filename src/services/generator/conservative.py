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
        members_by_id = {m.id: m for m in ctx.members}

        for ex in ctx.existing:
            assigned.add((ex.member_id, ex.date))
            st = ctx.all_shifts.get(ex.shift_type_id)
            if st and st.counts_as_work_time:
                mem = members_by_id.get(ex.member_id)
                member_hours[ex.member_id] += mem.hours_for(st) if mem else st.hours
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

                # Pattern short-circuit
                pcode = member.pattern_code_for(d)
                if pcode is not None:
                    pshift = ctx.shifts_by_code.get(pcode)
                    if pshift is not None:
                        proposals.append(ProposedAssignment(member.id, d, pshift.id))
                        assigned.add(key)
                        if pshift.counts_as_work_time:
                            member_hours[member.id] += member.hours_for(pshift)
                            member_last_work[member.id] = d
                    continue

                # Per-member work_days
                if not member.eligible_day(d):
                    if ctx.rest_shift_id:
                        proposals.append(ProposedAssignment(member.id, d, ctx.rest_shift_id))
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

                # Filter by coverage constraints + per-member shift rotation
                eligible = [s for s in ctx.work_shifts if member.eligible_shift(s.code)]
                if ctx.shift_coverage:
                    day_counts: dict[int, int] = defaultdict(int)
                    for ex in ctx.existing:
                        if ex.date == d:
                            day_counts[ex.shift_type_id] += 1
                    for p in proposals:
                        if p.date == d:
                            day_counts[p.shift_type_id] += 1

                    eligible = [s for s in eligible if not ctx.shift_coverage.get(s.id) or day_counts.get(s.id, 0) < ctx.shift_coverage[s.id].max]
                    needs = [s for s in eligible if ctx.shift_coverage.get(s.id) and day_counts.get(s.id, 0) < ctx.shift_coverage[s.id].min]
                    if needs:
                        eligible = needs

                if not eligible:
                    if ctx.rest_shift_id:
                        proposals.append(ProposedAssignment(member.id, d, ctx.rest_shift_id))
                    continue

                shift_idx = hash((member.id, d.toordinal())) % len(eligible)
                shift = eligible[shift_idx]

                proposals.append(ProposedAssignment(member.id, d, shift.id))
                assigned.add(key)
                member_hours[member.id] += member.hours_for(shift)
                member_last_work[member.id] = d

        return proposals
