"""
PCCM Moonlighter Night Schedule Optimizer
=========================================
Optimizes moonlighter night shift assignments based on faculty requests.

Key Differences from Standard Scheduler:
- Faculty REQUEST nights they WANT to work (not mark unavailable)
- Each faculty indicates desired number of nights
- Clinical effort is NOT a factor
- System assigns from requests to maximize fairness and coverage
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Set
from collections import defaultdict
import random


class MoonlighterScheduleOptimizer:
    """
    Assigns moonlighter night shifts based on faculty requests
    """
    
    def __init__(self, 
                 start_date: str,
                 end_date: str,
                 nights_per_coverage: int = 1):
        """
        Initialize the optimizer
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            nights_per_coverage: Number of faculty needed per night
        """
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.nights_per_coverage = nights_per_coverage
        
        # Generate all nights in the period
        self.nights = self._generate_nights()
        
        # Data structures
        self.faculty = {}  # faculty_id -> faculty data
        self.requests = defaultdict(list)  # night -> list of faculty_ids who requested it
        self.faculty_requests = defaultdict(set)  # faculty_id -> set of nights they requested
        self.desired_counts = {}  # faculty_id -> desired number of nights
        self.assignments = defaultdict(list)  # night -> list of assigned faculty_ids
        self.faculty_assignments = defaultdict(list)  # faculty_id -> list of assigned nights
        
    def _generate_nights(self) -> List[str]:
        """Generate list of all nights in the period"""
        nights = []
        current = self.start_date
        while current <= self.end_date:
            nights.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        return nights
    
    def load_faculty_requests(self, faculty_data: List[Dict]):
        """
        Load faculty moonlighter requests
        
        Expected format:
        [
            {
                'id': 'faculty_1',
                'name': 'Dr. Smith',
                'desired_nights': 10,  # How many nights they want
                'requested_dates': ['2024-11-05', '2024-11-10', ...],  # Nights they're willing to work
                'priority': 1  # Optional: 1=high, 2=medium, 3=low (for tie-breaking)
            }
        ]
        """
        for faculty in faculty_data:
            faculty_id = faculty['id']
            self.faculty[faculty_id] = faculty
            
            # Store desired count
            self.desired_counts[faculty_id] = faculty.get('desired_nights', 0)
            
            # Store requests (which nights they're willing to work)
            requested_dates = set(faculty.get('requested_dates', []))
            self.faculty_requests[faculty_id] = requested_dates
            
            # Build reverse index (night -> faculty who requested it)
            for night in requested_dates:
                if night in self.nights:
                    self.requests[night].append(faculty_id)
        
        print(f"✅ Loaded {len(self.faculty)} faculty with {sum(len(r) for r in self.faculty_requests.values())} total requests")
    
    def optimize_schedule(self, strategy: str = 'balanced') -> Dict:
        """
        Optimize the moonlighter schedule
        
        Args:
            strategy: 'balanced' (fairness), 'coverage' (maximize coverage), 
                     or 'satisfaction' (maximize faculty getting desired nights)
            
        Returns:
            Dictionary with schedule and metrics
        """
        if strategy == 'balanced':
            return self._optimize_balanced()
        elif strategy == 'coverage':
            return self._optimize_coverage_first()
        elif strategy == 'satisfaction':
            return self._optimize_satisfaction()
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _optimize_balanced(self) -> Dict:
        """
        Balanced optimization: Fair distribution while maximizing coverage
        
        Algorithm:
        1. Sort nights by number of requests (hardest to fill first)
        2. For each night, assign faculty who:
           - Requested it
           - Are furthest below their desired count
           - Have highest priority (if specified)
        """
        # Reset assignments
        self.assignments = defaultdict(list)
        self.faculty_assignments = defaultdict(list)
        
        # Track how many nights each faculty has been assigned
        assigned_counts = {fid: 0 for fid in self.faculty.keys()}
        
        # Sort nights by difficulty (fewest requests first = hardest to fill)
        nights_by_difficulty = sorted(self.nights, 
                                     key=lambda n: len(self.requests[n]))
        
        for night in nights_by_difficulty:
            available = self.requests[night]
            
            if not available:
                continue  # No one requested this night
            
            # Calculate "need score" for each available faculty
            # Higher score = more deserving
            scored_faculty = []
            for faculty_id in available:
                desired = self.desired_counts[faculty_id]
                assigned = assigned_counts[faculty_id]
                deficit = desired - assigned  # How far below target
                
                priority = self.faculty[faculty_id].get('priority', 2)
                priority_bonus = (4 - priority) * 10  # Priority 1 = +30, 2 = +20, 3 = +10
                
                score = deficit * 10 + priority_bonus
                scored_faculty.append((faculty_id, score, deficit))
            
            # Sort by score (highest first)
            scored_faculty.sort(key=lambda x: x[1], reverse=True)
            
            # Assign top N faculty
            for faculty_id, score, deficit in scored_faculty[:self.nights_per_coverage]:
                self.assignments[night].append(faculty_id)
                self.faculty_assignments[faculty_id].append(night)
                assigned_counts[faculty_id] += 1
        
        return self._generate_results()
    
    def _optimize_coverage_first(self) -> Dict:
        """
        Coverage-first optimization: Maximize number of nights covered
        
        Prioritizes covering as many nights as possible, even if distribution isn't perfect
        """
        self.assignments = defaultdict(list)
        self.faculty_assignments = defaultdict(list)
        
        assigned_counts = {fid: 0 for fid in self.faculty.keys()}
        
        # Sort nights by number of requests (fewest first)
        nights_sorted = sorted(self.nights, key=lambda n: len(self.requests[n]))
        
        for night in nights_sorted:
            available = self.requests[night]
            
            if not available:
                continue
            
            # Just take whoever is available, prioritizing those below target
            available_sorted = sorted(available, 
                                    key=lambda fid: assigned_counts[fid] - self.desired_counts[fid])
            
            # Assign first N available
            for faculty_id in available_sorted[:self.nights_per_coverage]:
                self.assignments[night].append(faculty_id)
                self.faculty_assignments[faculty_id].append(night)
                assigned_counts[faculty_id] += 1
        
        return self._generate_results()
    
    def _optimize_satisfaction(self) -> Dict:
        """
        Satisfaction optimization: Maximize faculty getting close to desired nights
        
        Uses Hungarian algorithm-like approach (greedy approximation)
        """
        self.assignments = defaultdict(list)
        self.faculty_assignments = defaultdict(list)
        
        assigned_counts = {fid: 0 for fid in self.faculty.keys()}
        
        # Process rounds: each round assigns one night to each faculty who wants more
        max_rounds = max(self.desired_counts.values()) if self.desired_counts else 0
        
        for round_num in range(max_rounds):
            # Find faculty who still want more nights
            active_faculty = [fid for fid in self.faculty.keys() 
                            if assigned_counts[fid] < self.desired_counts[fid]]
            
            if not active_faculty:
                break
            
            # Shuffle to avoid bias
            random.shuffle(active_faculty)
            
            # Each faculty tries to claim a night
            for faculty_id in active_faculty:
                # Get their requested nights that aren't full yet
                available_nights = [night for night in self.faculty_requests[faculty_id]
                                  if len(self.assignments[night]) < self.nights_per_coverage]
                
                if not available_nights:
                    continue
                
                # Pick the night with fewest other requests (least competition)
                best_night = min(available_nights, 
                               key=lambda n: len(self.requests[n]))
                
                # Assign it
                self.assignments[best_night].append(faculty_id)
                self.faculty_assignments[faculty_id].append(best_night)
                assigned_counts[faculty_id] += 1
        
        return self._generate_results()
    
    def _generate_results(self) -> Dict:
        """Generate results dictionary with schedule and metrics"""
        
        # Calculate metrics
        total_nights = len(self.nights)
        covered_nights = sum(1 for night in self.nights 
                           if len(self.assignments[night]) >= self.nights_per_coverage)
        partially_covered = sum(1 for night in self.nights 
                              if 0 < len(self.assignments[night]) < self.nights_per_coverage)
        uncovered_nights = total_nights - covered_nights - partially_covered
        
        # Faculty statistics
        faculty_stats = []
        for faculty_id, faculty in self.faculty.items():
            desired = self.desired_counts[faculty_id]
            assigned = len(self.faculty_assignments[faculty_id])
            requested = len(self.faculty_requests[faculty_id])
            
            # Calculate fulfillment rate
            fulfillment = (assigned / desired * 100) if desired > 0 else 0
            
            faculty_stats.append({
                'id': faculty_id,
                'name': faculty['name'],
                'requested': requested,  # How many nights they said they could work
                'desired': desired,  # How many they wanted to work
                'assigned': assigned,  # How many they got
                'difference': assigned - desired,
                'fulfillment': fulfillment,
                'nights': sorted(self.faculty_assignments[faculty_id])
            })
        
        # Find coverage gaps
        full_gaps = [night for night in self.nights 
                    if len(self.assignments[night]) == 0]
        partial_gaps = [night for night in self.nights 
                       if 0 < len(self.assignments[night]) < self.nights_per_coverage]
        
        # Calculate overall satisfaction
        total_desired = sum(self.desired_counts.values())
        total_assigned = sum(len(nights) for nights in self.faculty_assignments.values())
        overall_satisfaction = (total_assigned / total_desired * 100) if total_desired > 0 else 0
        
        metrics = {
            'total_nights': total_nights,
            'fully_covered': covered_nights,
            'partially_covered': partially_covered,
            'uncovered': uncovered_nights,
            'coverage_rate': (covered_nights / total_nights * 100),
            'total_shifts_needed': total_nights * self.nights_per_coverage,
            'total_shifts_filled': sum(len(assigned) for assigned in self.assignments.values()),
            'full_gaps': full_gaps,
            'partial_gaps': partial_gaps,
            'faculty_stats': faculty_stats,
            'overall_satisfaction': overall_satisfaction,
            'total_desired': total_desired,
            'total_assigned': total_assigned
        }
        
        return {
            'schedule': dict(self.assignments),
            'metrics': metrics
        }
    
    def export_to_csv(self, results: Dict, filename: str):
        """Export schedule to CSV"""
        rows = []
        for night, faculty_list in results['schedule'].items():
            for faculty_id in faculty_list:
                rows.append({
                    'date': night,
                    'faculty_id': faculty_id,
                    'faculty_name': self.faculty[faculty_id]['name']
                })
        
        if rows:
            df = pd.DataFrame(rows)
            df = df.sort_values('date')
            df.to_csv(filename, index=False)
            print(f"✅ Schedule exported to {filename}")
        else:
            print("⚠️  No assignments to export")
    
    def export_summary(self, results: Dict, filename: str):
        """Export summary statistics to CSV"""
        df = pd.DataFrame(results['metrics']['faculty_stats'])
        df = df.drop('nights', axis=1)  # Remove nights list for cleaner summary
        df.to_csv(filename, index=False)
        print(f"✅ Summary exported to {filename}")
    
    def export_request_analysis(self, results: Dict, filename: str):
        """Export detailed request analysis"""
        rows = []
        
        for night in self.nights:
            requesters = self.requests[night]
            assigned = self.assignments[night]
            
            rows.append({
                'date': night,
                'requests': len(requesters),
                'assigned': len(assigned),
                'filled': len(assigned) >= self.nights_per_coverage,
                'requesters': ', '.join([self.faculty[fid]['name'] for fid in requesters]),
                'assigned_faculty': ', '.join([self.faculty[fid]['name'] for fid in assigned])
            })
        
        df = pd.DataFrame(rows)
        df.to_csv(filename, index=False)
        print(f"✅ Request analysis exported to {filename}")
    
    def print_summary(self, results: Dict):
        """Print human-readable summary"""
        print("\n" + "="*70)
        print("MOONLIGHTER NIGHT SCHEDULE OPTIMIZATION SUMMARY")
        print("="*70)
        
        m = results['metrics']
        
        print(f"\n📊 COVERAGE METRICS:")
        print(f"   Total nights: {m['total_nights']}")
        print(f"   Fully covered: {m['fully_covered']} ({m['coverage_rate']:.1f}%)")
        print(f"   Partially covered: {m['partially_covered']}")
        print(f"   Uncovered: {m['uncovered']}")
        print(f"   Shifts needed: {m['total_shifts_needed']}")
        print(f"   Shifts filled: {m['total_shifts_filled']}")
        
        if m['full_gaps']:
            print(f"\n⚠️  UNCOVERED NIGHTS ({len(m['full_gaps'])}):")
            for gap in m['full_gaps'][:10]:
                print(f"   - {gap}")
            if len(m['full_gaps']) > 10:
                print(f"   ... and {len(m['full_gaps']) - 10} more")
        
        if m['partial_gaps']:
            print(f"\n⚠️  PARTIALLY COVERED ({len(m['partial_gaps'])} nights):")
            for gap in m['partial_gaps'][:5]:
                assigned_count = len(self.assignments[gap])
                print(f"   - {gap} ({assigned_count}/{self.nights_per_coverage} filled)")
            if len(m['partial_gaps']) > 5:
                print(f"   ... and {len(m['partial_gaps']) - 5} more")
        
        print(f"\n👥 FACULTY ASSIGNMENTS:")
        print(f"{'Name':<25} {'Requested':>10} {'Desired':>10} {'Assigned':>10} {'Diff':>8} {'Fulfill':>10}")
        print("-" * 70)
        
        for stat in sorted(m['faculty_stats'], key=lambda x: x['assigned'], reverse=True):
            diff_str = f"+{stat['difference']}" if stat['difference'] > 0 else str(stat['difference'])
            fulfill_str = f"{stat['fulfillment']:.0f}%"
            print(f"{stat['name']:<25} {stat['requested']:>10} {stat['desired']:>10} "
                  f"{stat['assigned']:>10} {diff_str:>8} {fulfill_str:>10}")
        
        print(f"\n📈 SATISFACTION METRICS:")
        print(f"   Total desired nights: {m['total_desired']}")
        print(f"   Total assigned nights: {m['total_assigned']}")
        print(f"   Overall satisfaction: {m['overall_satisfaction']:.1f}%")
        print(f"   (Higher = more faculty got close to desired nights)")
        
        print("\n" + "="*70 + "\n")


def example_usage():
    """
    Example of how to use the moonlighter optimizer
    """
    
    # Faculty request data
    # Each faculty indicates:
    # 1. How many nights they WANT to work
    # 2. Which specific nights they're WILLING to work
    faculty_data = [
        {
            'id': 'faculty_1',
            'name': 'Dr. Alice Smith',
            'desired_nights': 8,  # Wants 8 nights
            'requested_dates': [  # Available these nights
                '2024-11-01', '2024-11-02', '2024-11-03', '2024-11-04',
                '2024-11-08', '2024-11-09', '2024-11-10', '2024-11-11',
                '2024-11-15', '2024-11-16', '2024-11-17', '2024-11-18'
            ],
            'priority': 1  # High priority (senior faculty, etc.)
        },
        {
            'id': 'faculty_2',
            'name': 'Dr. Bob Johnson',
            'desired_nights': 10,
            'requested_dates': [
                '2024-11-05', '2024-11-06', '2024-11-07', '2024-11-12',
                '2024-11-13', '2024-11-14', '2024-11-19', '2024-11-20',
                '2024-11-21', '2024-11-26', '2024-11-27', '2024-11-28'
            ],
            'priority': 2  # Medium priority
        },
        {
            'id': 'faculty_3',
            'name': 'Dr. Carol Williams',
            'desired_nights': 5,
            'requested_dates': [
                '2024-11-01', '2024-11-05', '2024-11-10', '2024-11-15',
                '2024-11-20', '2024-11-25', '2024-11-29'
            ],
            'priority': 1
        },
        {
            'id': 'faculty_4',
            'name': 'Dr. David Brown',
            'desired_nights': 12,
            'requested_dates': [
                '2024-11-02', '2024-11-03', '2024-11-06', '2024-11-09',
                '2024-11-10', '2024-11-13', '2024-11-16', '2024-11-17',
                '2024-11-20', '2024-11-23', '2024-11-24', '2024-11-27',
                '2024-11-30'
            ]
        }
    ]
    
    # Create optimizer
    optimizer = MoonlighterScheduleOptimizer(
        start_date='2024-11-01',
        end_date='2024-11-30',
        nights_per_coverage=1
    )
    
    # Load requests
    optimizer.load_faculty_requests(faculty_data)
    
    # Optimize
    print("\n🔄 Running balanced optimization...")
    results = optimizer.optimize_schedule(strategy='balanced')
    
    # Print summary
    optimizer.print_summary(results)
    
    # Export results
    optimizer.export_to_csv(results, 'moonlighter_schedule.csv')
    optimizer.export_summary(results, 'moonlighter_summary.csv')
    optimizer.export_request_analysis(results, 'request_analysis.csv')
    
    return optimizer, results


if __name__ == '__main__':
    optimizer, results = example_usage()
