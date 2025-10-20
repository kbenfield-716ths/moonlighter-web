"""
Quick Runner for Moonlighter Night Schedule Optimizer
====================================================
This script makes it easy to run the moonlighter optimizer with your data.

Usage:
    python run_moonlighter.py

It will:
1. Load faculty moonlighter requests from CSV
2. Run optimization
3. Display results
4. Export to CSV files
"""

from moonlighter_optimizer import MoonlighterScheduleOptimizer
import pandas as pd
import sys
from datetime import datetime


def load_moonlighter_requests_from_csv(filename: str):
    """Load moonlighter requests from CSV file"""
    print(f"📂 Loading moonlighter requests from {filename}...")
    
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        print(f"❌ Error: Could not find {filename}")
        print(f"   Please create this file first using the template: moonlighter_template.csv")
        sys.exit(1)
    
    faculty_data = []
    
    for _, row in df.iterrows():
        faculty = {
            'id': row['faculty_id'],
            'name': row['name'],
            'desired_nights': int(row['desired_nights']),
        }
        
        # Parse requested dates
        if pd.notna(row.get('requested_dates')) and row['requested_dates'].strip():
            requested = [d.strip() for d in row['requested_dates'].split(',')]
            faculty['requested_dates'] = requested
        else:
            faculty['requested_dates'] = []
        
        # Optional: priority
        if pd.notna(row.get('priority')):
            faculty['priority'] = int(row['priority'])
        
        faculty_data.append(faculty)
    
    # Validate and report
    total_requests = sum(len(f['requested_dates']) for f in faculty_data)
    total_desired = sum(f['desired_nights'] for f in faculty_data)
    
    print(f"✅ Loaded {len(faculty_data)} faculty members")
    print(f"   Total night requests: {total_requests}")
    print(f"   Total desired nights: {total_desired}")
    
    return faculty_data


def run_moonlighter_optimization(
    faculty_data,
    start_date='2024-11-01',
    end_date='2024-11-30',
    nights_per_coverage=1,
    strategy='balanced'
):
    """Run the moonlighter optimization with given parameters"""
    
    print(f"\n⚙️  CONFIGURATION:")
    print(f"   Period: {start_date} to {end_date}")
    print(f"   Faculty per night: {nights_per_coverage}")
    print(f"   Strategy: {strategy}")
    
    # Create optimizer
    optimizer = MoonlighterScheduleOptimizer(
        start_date=start_date,
        end_date=end_date,
        nights_per_coverage=nights_per_coverage
    )
    
    # Load requests
    optimizer.load_faculty_requests(faculty_data)
    
    # Run optimization
    print(f"\n🔄 Running {strategy} optimization...")
    results = optimizer.optimize_schedule(strategy=strategy)
    
    return optimizer, results


def export_results(optimizer, results, output_prefix='moonlighter_schedule'):
    """Export results to CSV files"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    schedule_file = f"{output_prefix}_{timestamp}.csv"
    summary_file = f"{output_prefix}_summary_{timestamp}.csv"
    analysis_file = f"{output_prefix}_requests_{timestamp}.csv"
    
    optimizer.export_to_csv(results, schedule_file)
    optimizer.export_summary(results, summary_file)
    optimizer.export_request_analysis(results, analysis_file)
    
    return schedule_file, summary_file, analysis_file


def main():
    """Main execution function"""
    
    print("="*70)
    print("🌙 MOONLIGHTER NIGHT SCHEDULE OPTIMIZER")
    print("="*70)
    
    # ========================================
    # CONFIGURATION - Adjust these as needed
    # ========================================
    
    INPUT_FILE = 'moonlighter_input.csv'    # Your input CSV file
    START_DATE = '2024-11-01'               # First night to schedule
    END_DATE = '2024-11-30'                 # Last night to schedule
    NIGHTS_PER_COVERAGE = 1                 # How many faculty needed per night
    STRATEGY = 'balanced'                   # 'balanced', 'coverage', or 'satisfaction'
    
    # ========================================
    # RUN OPTIMIZATION
    # ========================================
    
    # Load data
    faculty_data = load_moonlighter_requests_from_csv(INPUT_FILE)
    
    # Run optimization
    optimizer, results = run_moonlighter_optimization(
        faculty_data,
        start_date=START_DATE,
        end_date=END_DATE,
        nights_per_coverage=NIGHTS_PER_COVERAGE,
        strategy=STRATEGY
    )
    
    # Display summary
    optimizer.print_summary(results)
    
    # Export results
    schedule_file, summary_file, analysis_file = export_results(optimizer, results)
    
    print(f"\n✅ COMPLETE!")
    print(f"   Schedule saved to: {schedule_file}")
    print(f"   Summary saved to: {summary_file}")
    print(f"   Request analysis saved to: {analysis_file}")
    print(f"\n💡 Next steps:")
    print(f"   1. Review the output files")
    print(f"   2. Check coverage gaps and faculty satisfaction")
    print(f"   3. Share with faculty for feedback")
    print(f"   4. Make adjustments if needed")
    
    # Provide strategy recommendations
    m = results['metrics']
    print(f"\n📊 OPTIMIZATION QUALITY:")
    print(f"   Coverage rate: {m['coverage_rate']:.1f}%")
    print(f"   Faculty satisfaction: {m['overall_satisfaction']:.1f}%")
    
    if m['coverage_rate'] < 90 and m['overall_satisfaction'] > 85:
        print(f"\n💡 Suggestion: Try strategy='coverage' to maximize coverage")
    elif m['overall_satisfaction'] < 80 and m['coverage_rate'] > 90:
        print(f"\n💡 Suggestion: Try strategy='satisfaction' to improve faculty fulfillment")
    
    return optimizer, results


if __name__ == '__main__':
    # Run the optimizer
    optimizer, results = main()
    
    # Optional: Compare strategies
    compare_strategies = False  # Set to True to compare all strategies
    
    if compare_strategies:
        print("\n\n" + "="*70)
        print("COMPARING ALL STRATEGIES")
        print("="*70)
        
        faculty_data = load_moonlighter_requests_from_csv('moonlighter_input.csv')
        
        for strategy in ['balanced', 'coverage', 'satisfaction']:
            print(f"\n\n--- STRATEGY: {strategy.upper()} ---")
            
            opt, res = run_moonlighter_optimization(
                faculty_data,
                strategy=strategy
            )
            
            opt.print_summary(res)
