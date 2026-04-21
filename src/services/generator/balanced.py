"""Balanced strategy: distributes shifts evenly, respects coverage min/max and all constraints."""

from collections import defaultdict
from datetime import date

from .base import GenerationContext, GenerationStrategy, ProposedAssignment


class BalancedStrategy(GenerationStrategy):
    def generate(self, ctx: GenerationContext) -> list[ProposedAssignment]:
        if not ctx.work_shifts or not ctx.members:
            return []

        assigned: dict[tuple[int, date], int] = {}
        locked_cells: set[tuple[int, date]] = set()
        member_hours: dict[int, float] = defaultdict(float)
        member_consecutive: dict[int, int] = defaultdict(int)
        member_last_work: dict[int, date | None] = {m.id: None for m in ctx.members}
        member_last_shift_id: dict[int, int | None] = {m.id: None for m in ctx.members}

        # Track shift counts per day for coverage
        day_shift_count: dict[tuple[date, int], int] = defaultdict(int)  # (date, shift_id) -> count

        members_by_id = {m.id: m for m in ctx.members}

        for ex in ctx.existing:
            assigned[(ex.member_id, ex.date)] = ex.shift_type_id
            if ex.is_locked:
                locked_cells.add((ex.member_id, ex.date))
            st = ctx.all_shifts.get(ex.shift_type_id)
            if st and st.counts_as_work_time:
                mem = members_by_id.get(ex.member_id)
                member_hours[ex.member_id] += mem.hours_for(st) if mem else st.hours
                member_last_work[ex.member_id] = ex.date
                member_last_shift_id[ex.member_id] = ex.shift_type_id
                day_shift_count[(ex.date, ex.shift_type_id)] += 1

        proposals: list[ProposedAssignment] = []
        total_days = len(ctx.dates)
        weeks = max(total_days / 7, 1)

        for d in ctx.dates:
            is_weekend = d.weekday() >= 5
            sorted_members = sorted(ctx.members, key=lambda m: member_hours[m.id])

            for member in sorted_members:
                key = (member.id, d)

                if ctx.fill_unassigned_only and key in assigned:
                    continue
                if key in locked_cells:
                    continue

                # Pattern short-circuit: if the member has a weekly_pattern, place
                # exactly that shift on this weekday and skip all other logic. The
                # human-designed pattern is the source of truth — we don't second-guess
                # it with coverage/consecutive/rest checks.
                pcode = member.pattern_code_for(d)
                if pcode is not None:
                    pshift = ctx.shifts_by_code.get(pcode)
                    if pshift is not None:
                        proposals.append(ProposedAssignment(member.id, d, pshift.id))
                        assigned[key] = pshift.id
                        if pshift.counts_as_work_time:
                            member_hours[member.id] += member.hours_for(pshift)
                            member_last_work[member.id] = d
                            member_last_shift_id[member.id] = pshift.id
                            day_shift_count[(d, pshift.id)] += 1
                    continue

                # Per-member work_days: if this weekday is outside the member's
                # eligible days, rest. Takes precedence over allow_weekend_work.
                if not member.eligible_day(d):
                    if ctx.rest_shift_id and key not in assigned:
                        proposals.append(ProposedAssignment(member.id, d, ctx.rest_shift_id))
                        assigned[key] = ctx.rest_shift_id
                    continue

                # Skip weekends if not allowed
                if is_weekend and not ctx.allow_weekend_work:
                    if ctx.rest_shift_id and key not in assigned:
                        proposals.append(ProposedAssignment(member.id, d, ctx.rest_shift_id))
                        assigned[key] = ctx.rest_shift_id
                    continue

                # Check weekly hour limit
                avg_weekly = member_hours[member.id] / weeks
                limit = min(ctx.weekly_hour_limit, member.weekly_hour_limit)
                if avg_weekly >= limit:
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
                    member_last_work[member.id] = None
                    continue

                # Check min rest hours
                last_shift = member_last_shift_id.get(member.id)
                if last_shift and last and (d - last).days == 1:
                    prev_st = ctx.all_shifts.get(last_shift)
                    if prev_st and prev_st.end_time:
                        eligible = [s for s in ctx.work_shifts if _rest_ok(prev_st.end_time, s.start_time, ctx.min_rest_hours)]
                        if not eligible:
                            if ctx.rest_shift_id and key not in assigned:
                                proposals.append(ProposedAssignment(member.id, d, ctx.rest_shift_id))
                                assigned[key] = ctx.rest_shift_id
                            continue
                    else:
                        eligible = ctx.work_shifts
                else:
                    eligible = ctx.work_shifts

                # Filter by member's allowed shift codes (e.g. "M 8 horas" only takes M)
                eligible = [s for s in eligible if member.eligible_shift(s.code)]
                if not eligible:
                    if ctx.rest_shift_id and key not in assigned:
                        proposals.append(ProposedAssignment(member.id, d, ctx.rest_shift_id))
                        assigned[key] = ctx.rest_shift_id
                    continue

                # Filter by coverage max — exclude shifts that already hit max for this day
                if ctx.shift_coverage:
                    eligible = [s for s in eligible if _under_max(ctx, d, s.id, day_shift_count)]
                    if not eligible:
                        if ctx.rest_shift_id and key not in assigned:
                            proposals.append(ProposedAssignment(member.id, d, ctx.rest_shift_id))
                            assigned[key] = ctx.rest_shift_id
                        continue

                # Pick shift: prefer shifts that need more coverage (under min), then rotate for balance
                if ctx.shift_coverage:
                    needs_coverage = [s for s in eligible if _under_min(ctx, d, s.id, day_shift_count)]
                    if needs_coverage:
                        eligible = needs_coverage

                shift_idx = hash((member.id, d.toordinal())) % len(eligible)
                shift = eligible[shift_idx]

                proposals.append(ProposedAssignment(member.id, d, shift.id))
                assigned[key] = shift.id
                member_hours[member.id] += member.hours_for(shift)
                member_last_work[member.id] = d
                member_last_shift_id[member.id] = shift.id
                day_shift_count[(d, shift.id)] += 1

        return proposals


def _rest_ok(prev_end: "time", next_start: "time | None", min_rest: int) -> bool:
    if not next_start:
        return True
    from datetime import timedelta
    end = timedelta(hours=prev_end.hour, minutes=prev_end.minute)
    start = timedelta(hours=next_start.hour, minutes=next_start.minute)
    rest = (timedelta(hours=24) - end) + start
    return rest.total_seconds() / 3600 >= min_rest


def _under_max(ctx: GenerationContext, d: date, shift_id: int, counts: dict) -> bool:
    cov = ctx.shift_coverage.get(shift_id)
    if not cov:
        return True
    return counts.get((d, shift_id), 0) < cov.max


def _under_min(ctx: GenerationContext, d: date, shift_id: int, counts: dict) -> bool:
    cov = ctx.shift_coverage.get(shift_id)
    if not cov:
        return False
    return counts.get((d, shift_id), 0) < cov.min
