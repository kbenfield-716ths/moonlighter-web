# 🌙 Moonlighter Night Schedule Optimizer - Complete Guide

## What's Different About This Version?

**This is for MOONLIGHTER scheduling**, not regular faculty scheduling!

### Key Differences

| Regular Scheduler | Moonlighter Scheduler |
|------------------|----------------------|
| Faculty mark dates UNAVAILABLE | Faculty REQUEST dates they WANT |
| Clinical effort determines targets | No clinical effort factor |
| System assigns to cover needs | System assigns from requests |
| Fair workload distribution | Fair opportunity distribution |

---

## 🎯 How It Works

### Faculty Provide:
1. **How many nights they want** (e.g., "I want 8 nights this month")
2. **Which nights they're available** (e.g., "I can work Nov 1, 5, 10, 15...")
3. **Optional priority level** (1=high, 2=medium, 3=low)

### System Optimizes:
- Assigns faculty to nights they requested
- Balances assignments fairly
- Maximizes coverage
- Respects everyone's desired count

---

## 🚀 Quick Start (3 Steps)

### Step 1: Gather Faculty Requests

Ask each faculty member:
- "How many moonlighter nights do you want this month?"
- "Which specific nights are you available to work?"

### Step 2: Fill in the CSV

Use `moonlighter_template.csv` as a starting point:

```csv
faculty_id,name,desired_nights,requested_dates,priority
faculty_1,Dr. Smith,8,"2024-11-01,2024-11-05,2024-11-10,2024-11-15...",1
faculty_2,Dr. Johnson,10,"2024-11-03,2024-11-07,2024-11-12...",2
```

**Important:** 
- `requested_dates` = nights they CAN work (comma-separated)
- `desired_nights` = how many they WANT
- `requested_dates` should typically be MORE than `desired_nights` (gives flexibility)

### Step 3: Run the Optimizer

```bash
python run_moonlighter.py
```

Done! Review the three output files.

---

## 📊 Understanding Your Results

### Three Output Files

**1. Schedule File** (`moonlighter_schedule_*.csv`)
```csv
date,faculty_id,faculty_name
2024-11-01,faculty_1,Dr. Smith
2024-11-02,faculty_4,Dr. Brown
...
```
→ Day-by-day assignments

**2. Summary File** (`moonlighter_schedule_summary_*.csv`)
```csv
id,name,requested,desired,assigned,difference,fulfillment
faculty_1,Dr. Smith,12,8,7,-1,87.5%
...
```
→ How each faculty did

**3. Request Analysis** (`moonlighter_schedule_requests_*.csv`)
```csv
date,requests,assigned,filled,requesters,assigned_faculty
2024-11-01,3,1,true,"Dr. Smith, Dr. Jones, Dr. Davis","Dr. Smith"
...
```
→ Competition for each night

### Key Metrics

**Coverage Rate:** % of nights filled (goal: 100%)
**Satisfaction:** % of desired nights achieved (goal: >80%)
**Fulfillment:** Per-faculty % of desired nights (goal: everyone 70%+)

---

## 🎛️ Three Optimization Strategies

### 1. Balanced (Default - Recommended)
```python
STRATEGY = 'balanced'
```
**Goal:** Fair distribution + good coverage  
**Best for:** Most situations  
**Result:** Everyone gets close to their desired count

### 2. Coverage-First
```python
STRATEGY = 'coverage'
```
**Goal:** Maximize nights covered  
**Best for:** When coverage is critical  
**Result:** Highest coverage rate, may sacrifice fairness

### 3. Satisfaction-First
```python
STRATEGY = 'satisfaction'
```
**Goal:** Make faculty happy  
**Best for:** When morale is important  
**Result:** More faculty hit their desired count, may leave gaps

### When to Switch Strategies

**Current Result** → **Try This Strategy**
- Coverage < 90%, Satisfaction > 85% → `'coverage'`
- Coverage > 95%, Satisfaction < 75% → `'satisfaction'`
- Both good → Stick with `'balanced'`

---

## 💡 Common Scenarios

### Scenario 1: Not Enough Requests

**Problem:** Only 20 nights requested, but need 30 nights covered

**Solutions:**
1. Ask faculty to indicate more available nights
2. Recruit additional moonlighters
3. Lower your coverage requirement (if possible)
4. Offer incentives for undersubscribed nights

### Scenario 2: Too Many Requests for Some Nights

**Problem:** Everyone wants Friday/Saturday, nobody wants Monday/Tuesday

**Solutions:**
1. Priority system helps (high-priority gets first pick)
2. Rotate desirable nights month-to-month
3. Differential pay for unpopular nights
4. Ask faculty to spread requests across all days

### Scenario 3: One Person Wants Way More Than Others

**Problem:** Dr. Smith wants 15 nights, everyone else wants 5

**Solutions:**
1. Let them! They'll get more if they requested more nights
2. Set a maximum if needed (cap at 12, for example)
3. Check if their requests conflict with others
4. This is usually not a problem - more eager = more shifts

### Scenario 4: Coverage Gaps on Holidays

**Problem:** Thanksgiving week has no requests

**Solutions:**
1. Offer holiday premium pay
2. Recruit specifically for holiday coverage
3. Rotate holiday duty year to year
4. Make holiday coverage a requirement (each person must request 1 holiday)

---

## 🔧 Advanced Configuration

### Pairs Required (2 per night)

```python
# In run_moonlighter.py
NIGHTS_PER_COVERAGE = 2
```

### Priority Levels

```csv
faculty_id,name,desired_nights,requested_dates,priority
faculty_1,Senior A,10,"...",1  # High - gets first pick
faculty_2,Mid-level,8,"...",2   # Medium
faculty_3,Junior,6,"...",3      # Low - fills remaining
```

### Custom Date Range

```python
START_DATE = '2024-12-01'  # December
END_DATE = '2024-12-31'
```

### Two-Month Schedule

```python
START_DATE = '2024-11-01'
END_DATE = '2024-12-31'  # Nov + Dec
```

---

## 📈 Analyzing Results

### Check Coverage Gaps

```python
results = optimizer.optimize_schedule()
gaps = results['metrics']['full_gaps']

if gaps:
    print(f"⚠️  Need coverage for: {gaps}")
    # Ask faculty to add these dates to their requests
```

### Check Fairness

```python
for stat in results['metrics']['faculty_stats']:
    fulfillment = stat['fulfillment']
    if fulfillment < 70:
        print(f"⚠️  {stat['name']} only got {fulfillment}% of desired nights")
        # They may need to request more nights
```

### Find Competition Hotspots

```python
# Look at request_analysis output
# Nights with high requests/assigned ratio = competitive
# Nights with low requests = need more volunteers
```

---

## 🎯 Best Practices

### 1. Give Clear Instructions to Faculty

**Good Email Template:**
```
Please provide your moonlighter availability for November:

1. How many nights do you want? (e.g., 8-10 nights)
2. Which nights can you work? List ALL nights you're available.
   - Provide MORE dates than you want (flexibility helps)
   - Example: "Available: Nov 1, 5, 7, 10, 12, 15, 18, 20, 22, 25, 28"
3. Priority level? (Optional: 1=need these shifts, 2=would like, 3=flexible)

Deadline: [Date]
```

### 2. Request More Than Needed

**Rule of thumb:** Faculty should list 2-3x their desired count

Example:
- Wants 8 nights → Should list 16-24 available nights
- Why? Gives optimizer flexibility to balance fairly

### 3. Set Realistic Expectations

Tell faculty:
- "We'll try to get you close to your desired count"
- "If you only list 8 nights and want 8, you'll probably get fewer"
- "More flexibility = better for everyone"

### 4. Handle Gaps Proactively

If optimizer shows gaps:
1. Email those specific dates to ALL faculty
2. Ask "Can anyone cover Nov 15?"
3. Update CSV with new requests
4. Re-run optimizer

### 5. Iterate

First run is a draft:
1. Run optimizer
2. Share results
3. Gather feedback ("I actually can't do Nov 10")
4. Update CSV
5. Re-run (takes seconds)
6. Repeat until finalized

---

## 🔄 Integration with Your System

### Export to Supabase

```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create table (one time)
"""
CREATE TABLE moonlighter_schedule (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  date DATE NOT NULL,
  faculty_id UUID REFERENCES faculty(id),
  schedule_type VARCHAR(50) DEFAULT 'moonlighter',
  status VARCHAR(20) DEFAULT 'scheduled',
  created_at TIMESTAMP DEFAULT NOW()
);
"""

# Upload schedule
for night, faculty_list in results['schedule'].items():
    for faculty_id in faculty_list:
        supabase.table('moonlighter_schedule').insert({
            'date': night,
            'faculty_id': faculty_id,
            'status': 'scheduled'
        }).execute()
```

### Add to Web App Admin Panel

```html
<!-- In admin.html -->
<div class="admin-card">
  <h2 class="card-title">Moonlighter Schedule</h2>
  
  <div class="form-group">
    <label>Month</label>
    <select id="moonlighterMonth">
      <option>November 2024</option>
      <option>December 2024</option>
    </select>
  </div>
  
  <div class="form-group">
    <label>Upload Faculty Requests (CSV)</label>
    <input type="file" id="moonlighterRequests" accept=".csv">
  </div>
  
  <button onclick="generateMoonlighterSchedule()">Generate Schedule</button>
  
  <div id="moonlighterResults" style="margin-top: 20px;"></div>
</div>
```

### Automated Email Notifications

```python
# After generating schedule
for faculty_id, nights in optimizer.faculty_assignments.items():
    faculty = optimizer.faculty[faculty_id]
    
    email_body = f"""
    Dear {faculty['name']},
    
    Your moonlighter schedule for November:
    
    Assigned Nights: {len(nights)}
    Desired Nights: {optimizer.desired_counts[faculty_id]}
    Fulfillment: {len(nights)/optimizer.desired_counts[faculty_id]*100:.0f}%
    
    Your nights:
    {chr(10).join(nights)}
    
    View full schedule: [link]
    """
    
    send_email(faculty['email'], "Moonlighter Schedule", email_body)
```

---

## 🐛 Troubleshooting

### Issue: Low satisfaction rate

**Problem:** Overall satisfaction < 70%

**Causes & Fixes:**
1. **Not enough total requests**
   - Total requested nights < total needed nights
   - Solution: Get more requests from faculty

2. **Requests don't overlap well**
   - Everyone wants different nights
   - Solution: Encourage broader availability

3. **Too many people want same nights**
   - Competition for popular nights
   - Solution: Priority system, or differential pay

4. **Strategy mismatch**
   - Using 'coverage' when should use 'satisfaction'
   - Solution: Switch strategies

### Issue: Coverage gaps

**Problem:** Some nights have no assignments

**Causes & Fixes:**
1. **Nobody requested those nights**
   - Solution: Email specifically about gaps, ask for volunteers

2. **Competition elsewhere**
   - System used faculty on other nights
   - Solution: Switch to 'coverage' strategy

3. **Not enough total faculty**
   - Mathematical impossibility
   - Solution: Recruit more moonlighters

### Issue: One person got way more than desired

**Problem:** Dr. Smith wanted 8, got 12

**Explanation:** This usually happens when:
- They requested many nights
- Those nights had little competition
- System needed to fill them

**Is this bad?** Usually no! They said they COULD work those nights.

**To prevent:** Set a maximum limit in code:
```python
# In optimizer, add cap
if assigned_counts[faculty_id] >= desired * 1.2:  # Cap at 120% of desired
    continue  # Skip this faculty
```

---

## 📋 Monthly Workflow Checklist

### Week 1 of Prior Month
- [ ] Email faculty requesting moonlighter availability
- [ ] Provide clear deadline (e.g., 10 days)
- [ ] Include instructions and examples

### Week 2 of Prior Month
- [ ] Send reminder email
- [ ] Answer any questions
- [ ] Collect responses in spreadsheet

### Week 3 of Prior Month
- [ ] Compile all requests into CSV
- [ ] Run optimizer with 'balanced' strategy
- [ ] Review results for issues

### Week 4 of Prior Month
- [ ] Share draft schedule with faculty
- [ ] Collect feedback for 2-3 days
- [ ] Make adjustments if needed
- [ ] Re-run optimizer

### Last Week of Prior Month
- [ ] Finalize schedule
- [ ] Export to your scheduling system
- [ ] Send confirmation emails
- [ ] Post schedule to shared location

### During Month
- [ ] Handle any swap requests
- [ ] Track no-shows or issues
- [ ] Use data to improve next month

---

## 📊 Comparison: Nov/Dec Example

Let's say you have 5 faculty for November (30 nights):

### Input Data:
```
Dr. Smith:   wants 8,  listed 12 available nights
Dr. Johnson: wants 10, listed 15 available nights
Dr. Williams wants 5,  listed 8 available nights
Dr. Brown:   wants 12, listed 18 available nights
Dr. Davis:   wants 6,  listed 10 available nights
Total wanted: 41 nights (> 30 needed ✅)
```

### Expected Results:
```
Coverage: 100% (30/30 nights filled)
Satisfaction: ~75-85%

Individual results:
Dr. Smith:   7-8 nights (87-100%)
Dr. Johnson: 8-10 nights (80-100%)
Dr. Williams 4-5 nights (80-100%)
Dr. Brown:   10-11 nights (83-92%)
Dr. Davis:   4-5 nights (67-83%)
```

### What affects who gets more?
1. Priority level (if specified)
2. Competition for their requested nights
3. Flexibility (more dates requested = more opportunities)

---

## 🎓 Understanding the Algorithm

### Balanced Strategy (Recommended)

**Step 1:** Sort nights by difficulty (fewest requests first)
- Nov 15: 2 requests (hard to fill)
- Nov 20: 5 requests (easy to fill)

**Step 2:** For each night, calculate "need score" for each requestor:
```
Score = (Desired - Assigned) × 10 + Priority Bonus
```

**Step 3:** Assign to highest-scoring faculty

**Why this works:**
- Fills hard nights first (ensures coverage)
- Gives priority to those below target (fairness)
- Respects priority levels (senior faculty, etc.)

### Coverage Strategy

- Prioritizes filling all nights
- Less concerned about perfect fairness
- Good when coverage is critical

### Satisfaction Strategy

- Each faculty gets "rounds" to pick nights
- Faculty with fewer assignments pick first
- Maximizes number hitting their target

---

## 🚀 Next Steps

### For Your Nov/Dec Schedule

1. **This week:** Send request email to faculty
2. **Next week:** Compile responses, run optimizer
3. **Following week:** Share draft, iterate
4. **Final week:** Publish final schedule

### For Future Months

1. Track which strategy works best
2. Note any patterns (holidays always gaps?)
3. Build historical database
4. Consider automated requests

### For Web Integration

1. Add moonlighter request form to web app
2. Faculty input directly (no CSV)
3. Run optimizer on button click
4. Display results in calendar view
5. Email notifications automated

---

## 📚 Files Included

- **moonlighter_optimizer.py** - Core engine
- **run_moonlighter.py** - Simple runner
- **moonlighter_template.csv** - Input template
- **This guide** - Complete documentation

---

## 💬 FAQs

**Q: What if nobody requests a critical night?**
A: That night shows as a gap. Email asking for volunteers, potentially offer premium.

**Q: Can I manually override assignments?**
A: Yes! Edit the output CSV before importing to your system.

**Q: What if someone changes their mind?**
A: Update the input CSV, re-run optimizer (takes seconds).

**Q: How is this different from regular scheduler?**
A: Regular scheduler works from unavailability and clinical effort. This works from requests and desires.

**Q: Can I use both systems?**
A: Yes! Use regular scheduler for daytime, moonlighter for nights.

**Q: What if I need 2 people per night?**
A: Set `NIGHTS_PER_COVERAGE = 2`

---

## ✨ Summary

**The Moonlighter Optimizer:**
- ✅ Assigns from faculty requests
- ✅ Balances fairly
- ✅ Maximizes coverage
- ✅ Respects preferences
- ✅ Fast and flexible
- ✅ Easy to iterate

**Perfect for:**
- Voluntary moonlighter shifts
- Extra coverage opportunities
- Supplemental scheduling
- Pay-per-shift systems

**Start with:** Template CSV + Run script = Results in seconds!

---

Ready to optimize your moonlighter schedule? Load your faculty requests and run it! 🚀
