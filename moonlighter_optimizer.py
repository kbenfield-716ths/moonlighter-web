
"""
Moonlighter Night Schedule Optimizer
------------------------------------
Assigns moonlighter nights based on requests and desired counts.

Input CSV expected columns:
- faculty_id
- name
- desired_nights (int)
- requested_dates (comma-separated YYYY-MM-DD)
- priority (optional int, 1=high,2=med,3=low; default 2)

Outputs (returned as dict from optimize() and also available via helper):
- schedule: {date: [faculty_id, ...]}
- metrics: {coverage_rate, avg_satisfaction, full_gaps, faculty_stats}
- summary: list of {id, name, desired, assigned, difference, fulfillment}
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter
import io
import pandas as pd

# How many people are required per night (1 by default)
NIGHT_SLOTS = 1

@dataclass
class Faculty:
    id: str
    name: str
    desired: int
    priority: int
    requests: Set[str]

class MoonlighterScheduleOptimizer:
    def __init__(self, df: pd.DataFrame, night_slots: int = NIGHT_SLOTS):
        self.night_slots = int(night_slots) if night_slots else 1
        self.faculty: Dict[str, Faculty] = {}
        self.requests_by_night: Dict[str, List[str]] = defaultdict(list)
        self.assignments_by_night: Dict[str, List[str]] = defaultdict(list)
        self.assigned_for_faculty: Dict[str, List[str]] = defaultdict(list)

        # Normalize DataFrame
        expected = {'faculty_id','name','desired_nights','requested_dates'}
        missing = expected - set(map(str, df.columns))
        if missing:
            raise ValueError(f"Missing required columns in CSV: {sorted(missing)}")

        def parse_dates(s: str) -> Set[str]:
            if pd.isna(s) or not str(s).strip():
                return set()
            parts = [p.strip() for p in str(s).split(',') if p.strip()]
            # Validate/normalize to YYYY-MM-DD
            out = set()
            for p in parts:
                try:
                    d = datetime.strptime(p, "%Y-%m-%d").date()
                    out.add(d.isoformat())
                except Exception:
                    # try mm/dd/yyyy
                    try:
                        d = datetime.strptime(p, "%m/%d/%Y").date()
                        out.add(d.isoformat())
                    except Exception:
                        # ignore bad entry
                        pass
            return out

        for _, row in df.iterrows():
            fid = str(row['faculty_id']).strip()
            name = str(row['name']).strip()
            desired = int(row['desired_nights']) if not pd.isna(row['desired_nights']) else 0
            prio = int(row['priority']) if 'priority' in df.columns and not pd.isna(row.get('priority', None)) else 2
            reqs = parse_dates(row['requested_dates'])
            self.faculty[fid] = Faculty(fid, name, desired, prio, reqs)
            for d in reqs:
                self.requests_by_night[d].append(fid)

        # Build the list of nights (union of all requests)
        self.all_nights: List[str] = sorted(self.requests_by_night.keys())

    def _need_score(self, fid: str) -> float:
        """Score used to prioritize who gets the next slot: higher = more need"""
        f = self.faculty[fid]
        assigned = len(self.assigned_for_faculty[fid])
        gap = f.desired - assigned
        # Priority bonus: 1=high -> +2, 2=med -> +1, 3=low -> +0
        prio_bonus = {1: 2.0, 2: 1.0, 3: 0.0}.get(f.priority, 1.0)
        return gap * 10.0 + prio_bonus

    def optimize(self, strategy: str = "balanced") -> Dict:
        """
        Strategies:
          - balanced: fill hard nights first, then assign by need score
          - coverage: prioritize nights with open slots and most requesters first
          - satisfaction: round-robin among faculty under target
        """
        # Nights difficulty (fewest requesters first)
        nights_sorted = sorted(self.all_nights, key=lambda d: len(self.requests_by_night[d]))

        if strategy not in {"balanced","coverage","satisfaction"}:
            strategy = "balanced"

        # assignment loop
        for night in nights_sorted:
            requesters = list(self.requests_by_night[night])
            if not requesters:
                continue

            # Sort candidates according to strategy
            if strategy == "balanced":
                # need score (higher first); tie-break: fewer assigned, then priority, then name
                requesters.sort(key=lambda fid: (self._need_score(fid), -len(self.faculty[fid].requests), -self.faculty[fid].priority, self.faculty[fid].name), reverse=True)
            elif strategy == "coverage":
                requesters.sort(key=lambda fid: (self.faculty[fid].priority, len(self.assigned_for_faculty[fid])), reverse=False)
            else: # satisfaction
                requesters.sort(key=lambda fid: (len(self.assigned_for_faculty[fid]), self.faculty[fid].priority))

            for fid in requesters:
                if len(self.assignments_by_night[night]) >= self.night_slots:
                    break
                f = self.faculty[fid]
                if len(self.assigned_for_faculty[fid]) >= f.desired and strategy != "coverage":
                    continue  # in satisfaction/balanced, don't exceed desired unless coverage strategy
                # Avoid double-booking same person multiple times in one night
                if fid in self.assignments_by_night[night]:
                    continue
                self.assignments_by_night[night].append(fid)
                self.assigned_for_faculty[fid].append(night)

            # coverage strategy: if still open slots, allow exceeding desired
            if strategy == "coverage" and len(self.assignments_by_night[night]) < self.night_slots:
                for fid in requesters:
                    if len(self.assignments_by_night[night]) >= self.night_slots:
                        break
                    if fid in self.assignments_by_night[night]:
                        continue
                    self.assignments_by_night[night].append(fid)
                    self.assigned_for_faculty[fid].append(night)

        return self._build_output()

    def _build_output(self) -> Dict:
        # Metrics
        total_slots = len(self.all_nights) * self.night_slots
        filled_slots = sum(len(v) for v in self.assignments_by_night.values())
        coverage = round(100.0 * filled_slots / total_slots, 1) if total_slots else 0.0

        faculty_stats = []
        satisfactions = []
        for f in self.faculty.values():
            assigned = len(self.assigned_for_faculty[f.id])
            desired = int(f.desired) if f.desired else 0
            fulfillment = round(100.0 * assigned / desired, 1) if desired else (100.0 if assigned==0 else 0.0)
            satisfactions.append(fulfillment if desired else 100.0)
            faculty_stats.append({
                "id": f.id,
                "name": f.name,
                "requested": len(f.requests),
                "desired": desired,
                "assigned": assigned,
                "difference": assigned - desired,
                "fulfillment": fulfillment,
            })

        avg_sat = round(sum(satisfactions) / len(satisfactions), 1) if satisfactions else 0.0

        schedule = {d: self.assignments_by_night[d] for d in sorted(self.assignments_by_night.keys())}
        gaps = [d for d in self.all_nights if len(self.assignments_by_night[d]) < self.night_slots]

        return {
            "schedule": schedule,
            "metrics": {
                "coverage_rate": coverage,
                "avg_satisfaction": avg_sat,
                "full_gaps": gaps,
                "faculty_stats": faculty_stats
            },
            "summary": faculty_stats
        }

# Convenience function to support Pyodide/web or CLI code
import io
import pandas as pd

def run_from_csv(csv_path: str, night_slots: int = 1, strategy: str = "balanced") -> dict:
    """Read and process the input CSV file safely."""
    try:
        # Try reading normally first
        df = pd.read_csv(csv_path)
    except Exception:
        try:
            # Retry with forgiving parser (handles extra commas, bad quotes)
            with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read().replace(", ", "; ")  # prevent comma splitting in names
            df = pd.read_csv(io.StringIO(text), engine="python", sep=",", on_bad_lines="skip")
        except Exception as e:
            raise ValueError(f"Unable to parse the uploaded CSV file. Please check formatting.\n\n{e}")

    # Validate columns
    required_cols = {"faculty_id", "name", "desired_nights", "requested_dates"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Missing required columns: {required_cols - set(df.columns)}")

    opt = MoonlighterScheduleOptimizer(df, night_slots=night_slots)
    return opt.optimize(strategy=strategy)
