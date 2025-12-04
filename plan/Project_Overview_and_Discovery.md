# The Langham Estate - Property Management System Project

**Date**: November 24, 2025  
**Status**: Discovery & Planning Phase

---

## Company Overview

**Name**: The Langham Estate  
**Location**: Fitzrovia, London  
**Portfolio**: ~80 buildings in Fitzrovia  
**Employees**: 40+ staff  
**IT Capability**: Minimal/none (part-time support only)

---

## Current Situation

### Property Portfolio Structure
- **80 buildings** across Fitzrovia
- Typical building layout:
  - Ground floor: Retail space
  - Floors 1-4: Office spaces
  - Usually **1 floor = 1 office unit** (sometimes 2 units per floor)
  - Total: 4-5 floors per building
  - **Estimated 300-400 total units** across portfolio

### Current "System" (Spreadsheet-Based)
**Format**: Single shared Excel/Google Sheet  
**Update Frequency**: Monthly  
**Distribution**: Email to all teams  
**Maintained by**: 1 person  

**Data Tracked**:
- Current tenant
- Lease start date
- Lease end date
- Space valuation
- Current rent
- Unit status (occupied/vacant/refurbishment)

**Critical Problems**:
- ❌ Month-old data (static snapshots)
- ❌ No real-time updates
- ❌ Email distribution (version control nightmare)
- ❌ Each team extracts/manipulates data separately
- ❌ High risk of errors
- ❌ No historical tracking
- ❌ No cross-department workflow
- ❌ No meaningful reporting/analytics

---

## Organizational Structure

### Departments Identified:
1. **Facilities Management (FM)**
2. **Marketing**
3. **Leasing**
4. **Accounting**
5. **Legal** (possibly)
6. **Surveyors**

### Current Software/Systems:
- **Propman**: Used by asset managers (property management software)
- **Agency Pilot**: CRM used by Leasing & Marketing teams
- **Website**: Run by Leasing/Marketing
- **Spreadsheet**: Shared across all departments (manual updates)

---

## Current Project: Weekly Report Module

**Purpose**: Pilot/proof-of-concept for larger system  
**Scope**: Monitor units in transition states:
- Leasing discussions in progress
- Refurbishment nearing completion
- Other state changes requiring attention

**Current Architecture**:
- Desktop application (PyQt6)
- SQLite database on shared LAN
- File-based locking system
- Planned migration: PostgreSQL + cloud backend

**Status**: Functional prototype with:
- Building & unit management
- Multi-user support with locking
- Audit logging
- Basic RBAC foundation (admin flag)
- Theme toggle
- Occupancy tracking

---

## Vision: Integrated Property Management Platform

### Goals:
1. **Centralized Database** - Single source of truth
2. **Real-time Updates** - No monthly email delays
3. **Department-Specific Views** - Each team sees relevant data
4. **Cross-Department Workflows** - Seamless information flow
5. **Historical Data** - Track changes over time
6. **Meaningful Reports** - Analytics and comparisons
7. **System Integration** - Connect with Propman, Agency Pilot
8. **Error Reduction** - Eliminate duplicate data entry
9. **Scalability** - Cloud-based, accessible anywhere

---

## Discovery Questions to Ask Client

### 1. DEPARTMENT WORKFLOWS

#### Facilities Management (FM):
- What specific data do they extract from the spreadsheet?
- What maintenance/refurbishment workflows exist?
- How do they track work orders?
- Who approves FM expenditures?
- How do they coordinate with tenants for access?
- What systems track service contracts (lifts, HVAC, security)?

#### Leasing:
- What's the complete leasing workflow? (Inquiry → Viewing → Negotiation → Contract)
- How are leads captured and tracked?
- Who approves lease terms?
- What data flows between Agency Pilot CRM and the spreadsheet?
- How do they track viewings and follow-ups?
- What happens when a lease is about to expire? (Renewal process)

#### Marketing:
- What property information goes on the website?
- How often is website updated?
- Is Agency Pilot the source of truth for available units?
- How do they track marketing campaigns per property?
- What reports do they need? (Inquiries, conversion rates, time-to-let)

#### Accounting:
- What financial data do they track beyond rent?
- How are invoices generated?
- What's the rent collection process?
- How do they handle service charges?
- What financial reports are needed? (P&L per building, cashflow, arrears)
- Integration with accounting software (Xero, Sage, QuickBooks)?

#### Surveyors:
- What valuations do they perform?
- How often are properties revalued?
- What data do they need for valuations?
- How are surveys/inspections tracked?
- Who receives survey reports?

#### Legal:
- How are contracts managed?
- Who reviews lease agreements?
- How are legal issues tracked?
- Where are documents stored?

---

### 2. DATA & SYSTEMS INTEGRATION

#### Propman (Asset Management Software):
- What data is stored in Propman?
- Can it export data? (API, CSV, database access?)
- Who has access to Propman?
- Is it used for all buildings or subset?
- Does it track financials?
- Does it handle lease management?

#### Agency Pilot (CRM):
- What data is in Agency Pilot?
- API available?
- Does it track both inquiries AND active leases?
- Integration with website?
- Who uses it daily?

#### Current Spreadsheet:
- Can I see the actual spreadsheet structure?
- How many columns/fields?
- What calculations/formulas exist?
- Are there multiple sheets/tabs?
- Who updates it and how often in reality?

---

### 3. APPROVAL WORKFLOWS

**Critical to understand**:
- Who approves new leases?
- Who approves rent changes?
- Who approves refurbishment budgets?
- Who approves lease renewals?
- What's the hierarchy? (Agent → Manager → Director?)
- Are there financial thresholds for different approval levels?

---

### 4. REPORTING NEEDS

**By Department**:
- What reports does each department currently create manually?
- What metrics matter most?
- How often are reports needed?
- Who receives reports? (Internal vs. Board/Investors)

**Examples to explore**:
- Vacancy rates (overall, by building, by floor type)
- Rent roll (current vs. budget vs. previous year)
- Lease expiry schedule (next 3/6/12 months)
- Tenant turnover rates
- Time to let (vacant → occupied)
- Refurbishment spend vs. budget
- Rent arrears

---

### 5. TECHNICAL CONSTRAINTS

- What's the network setup? (VPN access? Cloud restrictions?)
- Desktop vs. Web application preference?
- Mobile access needed?
- Security/compliance requirements? (GDPR, financial data)
- Backup/disaster recovery expectations?
- Budget for cloud hosting?
- IT support availability for rollout/training?

---

### 6. CHANGE MANAGEMENT

- How resistant to change are teams?
- Who are the key stakeholders/decision makers?
- What's failed before? (Previous IT projects?)
- Training expectations?
- Rollout preference? (Big bang vs. phased by department?)
- Who will champion the new system?

---

### 7. BUILDING/UNIT DATA MODEL

**Need to clarify**:
- How are buildings identified? (Name, address, internal code?)
- How are units numbered? (Floor-based? Sequential?)
- Are there sub-units? (Office divided into smaller spaces?)
- Common areas tracked separately?
- Parking spaces tracked?
- Storage units?
- What unit attributes are critical?
  - Square footage (retail vs. office)
  - Ceiling height
  - Access (shared entrance, dedicated)
  - Condition/grade (A, B, C)
  - Planning use class

---

### 8. LEASE COMPLEXITY

- Standard lease terms? (FRI, internal repairing?)
- Rent review mechanisms? (Fixed increase, RPI, market review)
- Break clauses?
- Service charges - how calculated and billed?
- Rent-free periods tracked?
- Tenant incentives?
- Guarantors/deposits?

---

### 9. COMPLIANCE & DOCUMENTATION

- Where are contracts stored? (Physical, digital, both?)
- Document management system exists?
- How are certificates tracked? (EPC, Gas Safety, Fire Risk Assessment)
- Insurance documentation?
- Planning permissions?

---

### 10. PRIORITIES & TIMELINE

- What's the pain point priority?
  1. Real-time data access?
  2. Workflow automation?
  3. Reporting?
  4. Integration with existing systems?
  
- What's the timeline expectation?
- Phase 1 scope? (MVP)
- Budget constraints?
- Success criteria? (How will they measure if project successful?)

---

## Preliminary Recommendations (Pre-Discovery)

### Phase 1: Foundation (Current Weekly Report + RBAC)
**Timeline**: 2-3 months  
**Scope**:
- Enhance current prototype
- Implement full RBAC system
- Add workflow/approval system
- Improve reporting
- Deploy on LAN for pilot users

**Benefits**:
- Quick win - something working soon
- Learn actual user needs
- Test before big investment

### Phase 2: Integration Layer
**Timeline**: 2-3 months  
**Scope**:
- Migrate to PostgreSQL + cloud
- Build API for future integrations
- Connect to Propman (read-only initially?)
- Connect to Agency Pilot (sync leads/leases)

**Benefits**:
- Eliminate duplicate data entry
- Single source of truth
- Real-time synchronization

### Phase 3: Department Modules
**Timeline**: 3-6 months  
**Scope**:
- Custom views per department
- Advanced workflows
- Document management
- Mobile access
- Advanced reporting/analytics

**Benefits**:
- Replace spreadsheet entirely
- Full digital transformation

---

## Key Risks to Explore

1. **Data Quality**: Is current spreadsheet data accurate enough to migrate?
2. **User Adoption**: Will 40+ users embrace new system?
3. **Integration Complexity**: Can Propman/Agency Pilot actually integrate?
4. **Scope Creep**: Project could explode in size
5. **Resource Constraint**: You're part-time, no IT team
6. **Hidden Workflows**: Undocumented processes that break when digitized

---

## Success Factors

✅ **Executive Sponsorship**: Need a champion at leadership level  
✅ **User Involvement**: Include actual users in design  
✅ **Phased Approach**: Don't try to do everything at once  
✅ **Quick Wins**: Show value early and often  
✅ **Training Plan**: Can't just deploy and hope  
✅ **Data Migration Strategy**: Clean data before launch  
✅ **Support Plan**: Who fixes issues after launch?  

---

## Questions for Immediate Next Steps

1. **Can you schedule interviews with each department head?**
   - 30-60 min each
   - Understand their workflows
   - See their current tools

2. **Can you access the current spreadsheet?**
   - Analyze structure
   - Understand data model
   - Identify gaps

3. **Can you get demo access to Propman and Agency Pilot?**
   - See their data models
   - Check integration possibilities
   - Understand what they solve well

4. **Who's the decision maker?**
   - Who approves budget?
   - Who defines requirements?
   - Who signs off on project?

5. **What's the budget range?**
   - Development time
   - Cloud hosting costs
   - Training
   - Ongoing support

6. **Timeline expectations?**
   - When do they want to start using something?
   - Any business drivers? (Investor reporting, audit requirements)

---

## My Initial Questions for You

### About Current Weekly Report Usage:
1. **Who actually uses the weekly report prototype?**
   - Which departments?
   - How many users?
   - What feedback have you received?

2. **What prompted the weekly report request?**
   - Specific business problem?
   - Regulatory requirement?
   - Someone's pet project?

### About Your Role:
3. **What's your official role?**
   - Consultant?
   - Part-time employee?
   - Contractor?

4. **How many hours per week can you dedicate?**

5. **Do they expect you to maintain this long-term?**
   - Or just build it and hand off?
   - Is there a plan to hire IT staff?

### About Decision Making:
6. **Who asked you to build this?**
   - Their title/department?
   - Do they have budget authority?

7. **Have you presented a formal proposal?**
   - Or is this exploratory?

8. **What's their tech literacy level?**
   - Comfortable with change?
   - Resistant?

### About Existing Systems:
9. **Is Propman used by all asset managers or just some?**

10. **Is Agency Pilot cloud-based or on-premise?**

11. **Do they have an IT vendor/consultant currently?**
    - For Propman support?
    - Network management?

12. **What's their cloud stance?**
    - Open to SaaS?
    - Data sovereignty concerns?
    - Security policies?

### About Data:
13. **Do you have access to sample data?**
    - Can I see the spreadsheet?
    - Anonymized is fine

14. **How accurate is the "1 person updates monthly" description?**
    - Is it really that broken?
    - Or is it "mostly works but could be better"?

15. **What data quality issues exist?**
    - Duplicate entries?
    - Missing data?
    - Inconsistent formatting?

---

## Next Actions (Recommended)

1. **Schedule stakeholder interviews** - One per department head
2. **Data audit** - Analyze current spreadsheet structure
3. **System demos** - Get access to Propman and Agency Pilot
4. **Create visual diagrams** - Current state vs. future state
5. **Draft formal proposal** - With phases, timeline, costs
6. **Build business case** - ROI, efficiency gains, risk reduction

---

## Notes

This is a **classic digital transformation project** disguised as a "simple property management system."

**Scope is potentially massive**, but smart phasing can make it achievable.

**Your current prototype is perfect** for Phase 1 proof-of-concept.

**Key insight**: They don't just need software - they need **business process redesign**. The spreadsheet isn't the problem, it's a symptom of undefined workflows.

**Strategic approach**: 
1. Solve one department's pain really well (quick win)
2. Expand to adjacent department
3. Build integration layer
4. Eventually replace spreadsheet entirely

**Risk mitigation**: Don't promise to replace everything at once. Position as **"Modern tools to complement your existing systems"** initially.

---

**This is a great opportunity**, but needs careful scoping to avoid:
- Feature creep
- Analysis paralysis  
- Over-promising
- Building something nobody uses

Let's discuss your answers to my questions and I can help you create a solid discovery plan and proposal!
