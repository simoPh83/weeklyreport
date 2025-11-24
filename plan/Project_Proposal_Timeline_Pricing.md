# The Langham Estate - Project Proposal & Timeline

**Date**: November 24, 2025  
**Prepared for**: The Langham Estate Board  
**Project**: Integrated Property Management System

---

## Executive Summary

**Current Situation**: 200 units tracked in monthly-updated spreadsheet with ~20 data fields, distributed via email. Data silos across 6+ departments creating inefficiencies, errors, and limited reporting capability.

**Proposed Solution**: Phased implementation of centralized property management system, starting with Weekly Report module (already prototyped) and expanding to full integration.

**Your Capacity**: 2 days/week (16 hours/week) dedicated to development

**Timeline**: 12-18 months for complete system (phased delivery)

**Investment Range**: £15,000 - £45,000 depending on scope (see options below)

---

## Current Data Estate

- **~200 active units** across 80 buildings
- **~20 data fields** per unit in current spreadsheet
- **10 years of historical data** in various formats
- **Monthly update cycle** (significant lag)
- **6+ departments** using different extracts
- **2 existing systems**: Propman (asset management), Agency Pilot (CRM)

---

## Three Proposal Options

### 🎯 OPTION 1: Weekly Report + Foundation (RECOMMENDED START)

**Scope**: Deliver the requested weekly report PLUS build foundation for future expansion

#### Deliverables:
1. **Weekly Report Module** (Enhanced current prototype)
   - Track unit status changes week-over-week
   - Calculate rent/sqft changes automatically
   - Rent vs evaluation analysis
   - Automated report generation (PDF/Excel)
   - Multi-user access with permissions
   
2. **Core Data Platform**
   - Migrate 200 units + buildings to proper database
   - Import current spreadsheet data
   - Basic historical data (last 12 months)
   - Real-time updates (not monthly lag)
   - Audit trail for all changes
   
3. **User Management**
   - Role-based access (Admin, Manager, Viewer)
   - 5-10 user accounts
   - LAN-based deployment (existing infrastructure)

#### Timeline: **3 months** (12 weeks × 16 hours = 192 hours)
- Week 1-2: Requirements & data analysis
- Week 3-6: Core development & testing
- Week 7-9: Historical data migration
- Week 10-11: User testing & refinement
- Week 12: Training & deployment

#### Investment: **£15,000**
- Based on 192 hours @ £78/hour
- Includes training materials
- 1 month post-launch support

#### Risk: **LOW** - Builds on working prototype, limited scope, quick win

---

### 🚀 OPTION 2: Complete Department Solution (Leasing Focus)

**Scope**: Option 1 PLUS full leasing workflow and Agency Pilot integration

#### Additional Deliverables:
1. **Leasing Workflow Module**
   - Lead tracking (inquiry → viewing → negotiation → contract)
   - Lease lifecycle management (start, renewal, termination)
   - Document management (contracts, notices)
   - Approval workflows (manager sign-off)
   - Email notifications
   
2. **Agency Pilot Integration**
   - Two-way sync with CRM
   - Automatic lead import
   - Status updates (available → under offer → let)
   - Eliminate duplicate data entry
   
3. **Advanced Reporting**
   - Vacancy analysis (by building, floor type, time period)
   - Time-to-let metrics
   - Conversion rates (inquiry → lease)
   - Rent roll reports
   - Lease expiry schedule (3/6/12 months)
   - Historical comparisons (YoY, QoQ)
   
4. **Historical Data Migration**
   - Import 3-5 years of historical data
   - Data cleaning & validation
   - Trend analysis capability

#### Timeline: **6 months** (26 weeks × 16 hours = 416 hours)
- Month 1-2: Option 1 delivery
- Month 3: Agency Pilot integration & testing
- Month 4: Leasing workflow development
- Month 5: Historical data migration (3-5 years)
- Month 6: Advanced reporting & training

#### Investment: **£28,000**
- 416 hours @ £67/hour
- Agency Pilot integration (API access fees if any)
- Extended training program
- 2 months post-launch support

#### Risk: **MEDIUM** - Depends on Agency Pilot API availability

---

### 🏢 OPTION 3: Enterprise Platform (All Departments)

**Scope**: Complete digital transformation - replace spreadsheet entirely

#### Complete System Including:
1. **All Option 2 Features**

2. **Multi-Department Modules**
   - **Facilities Management**: Work orders, maintenance tracking, service contracts
   - **Accounting**: Rent invoicing, payment tracking, arrears management
   - **Marketing**: Website integration, campaign tracking, availability updates
   - **Surveyors**: Valuation tracking, inspection scheduling, report management
   
3. **Cloud Migration**
   - PostgreSQL cloud database
   - REST API backend (FastAPI)
   - Web-based access (anywhere, anytime)
   - Mobile-responsive design
   - Automatic backups & disaster recovery
   
4. **Propman Integration**
   - Financial data sync (if API available)
   - Building/unit master data
   - Avoid duplicate data entry
   
5. **Complete Historical Archive**
   - 10 years of data imported
   - Data normalization (handle format changes)
   - Full audit trail
   
6. **Advanced Features**
   - Dashboard with KPIs
   - Custom report builder
   - Automated email reports
   - Document storage (contracts, certificates)
   - Calendar integration (lease events, inspections)
   - Export to Excel/PDF

#### Timeline: **12-15 months** (52-65 weeks × 16 hours = 832-1040 hours)
- Month 1-6: Core platform + Leasing module (Option 2)
- Month 7-8: Cloud migration & API development
- Month 9-10: FM & Accounting modules
- Month 11-12: Marketing & Surveyor modules
- Month 13-14: Propman integration
- Month 15: Complete historical data migration, testing, training

#### Investment: **£45,000 - £55,000**
- Development: 900 hours @ £50/hour = £45,000
- Cloud hosting: £100-200/month (£2,400/year included in first year)
- Third-party API costs: £500-1,500/year (estimated)
- Comprehensive training program
- 6 months post-launch support

#### Risk: **HIGHER** - Complex integrations, scope creep potential, long timeline

---

## Detailed Cost Breakdown (Option 1 - Recommended Start)

### Development Hours: 192 hours

| Phase | Hours | Tasks |
|-------|-------|-------|
| **Discovery & Planning** | 16h | Requirements gathering, spreadsheet analysis, data model design |
| **Core Development** | 80h | Database schema, business logic, UI enhancements, weekly report generation |
| **Data Migration** | 32h | Import current data, clean/validate, import 12 months history |
| **Testing & QA** | 24h | Unit testing, integration testing, user acceptance testing |
| **Documentation** | 16h | User manual, admin guide, technical documentation |
| **Training** | 16h | Training materials, live sessions, support handover |
| **Deployment & Support** | 8h | Installation, initial support, bug fixes |

### Investment: £15,000
- Hourly rate: £78 (192 hours)
- Includes 1 month post-launch support (16 hours)
- No ongoing hosting costs (LAN-based)

---

## Phased Investment Strategy (RECOMMENDED)

**Smart Approach**: Don't commit to everything upfront. Prove value at each stage.

### Phase 1: Quick Win (3 months - £15,000)
✅ Deliver weekly report as requested  
✅ Build proper foundation  
✅ Prove concept  
✅ Get user feedback  
✅ **Decision point**: Continue or stop

### Phase 2: Leasing Excellence (3 months - £13,000 additional)
✅ Full leasing workflow  
✅ Agency Pilot integration  
✅ Historical data (3 years)  
✅ Advanced reporting  
✅ **Decision point**: Expand to other departments or optimize current

### Phase 3: Enterprise Scale (6-9 months - £17,000-27,000 additional)
✅ Cloud migration  
✅ Multi-department modules  
✅ Propman integration  
✅ Complete historical archive  

**Total Phased Investment**: £45,000-55,000 over 12-15 months  
**Risk Mitigation**: Can stop after any phase if ROI not demonstrated

---

## Return on Investment (ROI) Analysis

### Current Costs (Hidden/Opportunity)

**Time Waste**:
- 1 person updates spreadsheet monthly: **8 hours/month** = £240/month (@ £30/hour)
- 6 departments extract/manipulate data: **6 × 4 hours/month** = £720/month
- Manual report creation: **8 hours/week** = £960/month
- **Total**: ~£1,920/month = **£23,040/year**

**Error Costs**:
- Missed lease renewals (1-2 per year): **£20,000-50,000/year**
- Vacant units due to poor tracking: **£10,000+/year**
- Marketing budget waste (wrong availability data): **£5,000/year**

**Opportunity Costs**:
- Delayed decision making (month-old data)
- Inability to optimize rent pricing
- No meaningful analytics for strategy

### Estimated Annual Savings with New System

| Category | Annual Saving |
|----------|---------------|
| Staff time savings (automation) | £20,000 |
| Reduced errors (missed renewals) | £15,000 |
| Better vacancy management | £10,000 |
| Improved decision making | £25,000+ |
| **Total Estimated Savings** | **£70,000/year** |

### ROI Calculation (Option 1)

**Investment**: £15,000  
**Annual Savings**: £30,000 (conservative - just time savings)  
**Payback Period**: **6 months**  
**3-Year ROI**: 500%+

---

## Technical Architecture

### Current Prototype (Already Built)
- PyQt6 desktop application
- SQLite database
- File-based locking (multi-user)
- Audit logging
- Theme toggle (dark/light)
- RBAC foundation

### Phase 1 Architecture
- **Same as prototype** + enhancements
- Deployed on LAN (existing infrastructure)
- No cloud costs
- Windows desktop application

### Phase 2+ Architecture (Cloud Migration)
- **Backend**: FastAPI + PostgreSQL (AWS/Digital Ocean)
- **Frontend**: Web application (React) + Desktop (PyQt6)
- **API**: RESTful for integrations
- **Security**: JWT auth, encrypted connections
- **Hosting**: ~£100-200/month

---

## Risk Assessment & Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Agency Pilot API unavailable | Medium | Medium | Manual sync option, CSV import/export |
| Propman integration complex | High | Low | Phase 3 only, can skip if needed |
| Data quality issues | High | Medium | Extensive data cleaning phase |
| Historical data format changes | High | Medium | Semi-automated import with validation |
| User adoption resistance | Medium | High | Phased rollout, extensive training |

### Business Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Scope creep | High | High | Fixed scope per phase, change control |
| Resource availability (your time) | Medium | High | Buffer built into timeline |
| Budget constraints | Low | High | Phased approach, can stop anytime |
| Competing priorities | Medium | Medium | Executive sponsorship critical |

---

## Success Criteria

### Phase 1 Success Metrics (3 months):
- ✅ Weekly report generated in < 5 minutes (vs. current 2+ hours manual)
- ✅ Real-time data (vs. month-old)
- ✅ 5+ users actively using system
- ✅ Zero data loss/corruption
- ✅ 90%+ user satisfaction

### Phase 2 Success Metrics (6 months):
- ✅ Agency Pilot sync working (< 5 min delay)
- ✅ Lease workflow adopted by leasing team (100% usage)
- ✅ 50% reduction in duplicate data entry
- ✅ Historical trend reports available

### Phase 3 Success Metrics (12-15 months):
- ✅ Spreadsheet fully replaced
- ✅ All 6 departments using system
- ✅ 80%+ time savings on manual tasks
- ✅ Executive dashboard with KPIs

---

## Resource Requirements

### From The Langham Estate:

**Essential**:
- Executive sponsor (decision maker)
- Access to current spreadsheet + historical data
- Demo access to Propman & Agency Pilot
- 1-2 hours/week from department heads (requirements/feedback)
- Testing time from end users (2-4 hours/week during UAT)

**Helpful**:
- IT support for network access/deployment
- Budget approval process clarity
- Document access (sample contracts, reports)

### From You (Developer):

- **16 hours/week** dedicated development time
- Project management (tracking, communication)
- Development environment (already setup)
- Testing & QA
- Documentation
- Training delivery

---

## Project Governance

### Recommended Structure:

**Steering Committee** (Monthly meetings):
- Executive sponsor
- Leasing manager
- FM manager
- You (project lead)

**Working Group** (Weekly updates):
- Department representatives (1 from each)
- You (developer)

**Communication**:
- Weekly progress emails
- Monthly demos
- Bi-weekly check-ins with sponsor

---

## Dependencies & Assumptions

### Assumptions:
- Network infrastructure adequate for LAN deployment
- Current data reasonably accurate (80%+)
- Users have Windows PCs
- Agency Pilot has export/import capability (even if manual)
- Board approval for project within 4 weeks
- Start date within 2 months

### Dependencies:
- Access to systems/data provided within 2 weeks of start
- User availability for testing (Phase 1: Week 10-11)
- Timely feedback on deliverables (< 1 week turnaround)
- Decision making (not delayed by committees)

---

## Payment Terms (Suggested)

### Option 1 (£15,000):
- **£5,000** - Upon contract signing (Discovery & Planning)
- **£5,000** - Mid-project (End of Week 6 - Core dev complete)
- **£5,000** - Upon deployment (End of Week 12)

### Option 2 (£28,000):
- **£7,000** - Upon contract signing
- **£7,000** - End of Month 2 (Option 1 complete)
- **£7,000** - End of Month 4 (Integration complete)
- **£7,000** - Upon deployment (End of Month 6)

### Option 3 (£45,000-55,000):
- **Quarterly milestones**: £11,250-13,750 per quarter
- Or **monthly**: £3,750-4,500/month

---

## Comparison: Build vs. Buy

### Off-the-Shelf Property Management Software

**Options**: Yardi, MRI, AppFolio, Re-Leased, etc.

**Typical Costs**:
- Setup: £10,000-30,000
- Per user/month: £50-150
- Annual: **£30,000-90,000** (for 40 users)
- Customization: £££ (often difficult/impossible)

**Advantages of Custom Build**:
- ✅ Exact fit for your workflows
- ✅ Integration with existing systems (Agency Pilot, Propman)
- ✅ Lower long-term cost
- ✅ No per-user fees
- ✅ Full control over features
- ✅ UK-based, in-house support

**Advantages of Off-the-Shelf**:
- ✅ Faster deployment (if fits)
- ✅ Proven at scale
- ✅ Regular updates
- ✅ Dedicated support team

---

## Timeline Visualization

### Option 1: 3 Months
```
Month 1           Month 2           Month 3
├─────────────────┼─────────────────┼─────────────────┤
Discovery         Core Dev          Testing & Deploy
Planning          Migration         Training
Data Analysis     UI Polish         Support
```

### Option 2: 6 Months
```
Month 1-2         Month 3-4         Month 5-6
├─────────────────┼─────────────────┼─────────────────┤
Option 1          Integration       Historical Data
Delivery          Leasing Module    Advanced Reports
                  Testing           Training
```

### Option 3: 12-15 Months
```
Q1 (M1-3)         Q2 (M4-6)         Q3 (M7-9)         Q4 (M10-12)       Q5 (M13-15)
├─────────────────┼─────────────────┼─────────────────┼─────────────────┼──────────┤
Option 1          Option 2          Cloud Migration   Dept Modules      Historical
Weekly Report     Leasing Focus     API Development   FM/Accounting     10yr Data
Foundation        Agency Pilot      Web Frontend      Marketing/Survey  Integration
                                                      Propman           Training
```

---

## Recommendation & Next Steps

### My Recommendation: **Option 1 → Option 2 (Phased)**

**Why**:
1. ✅ **Quick win** - Delivers requested weekly report in 3 months
2. ✅ **Proves value** - Board sees ROI before committing more
3. ✅ **Builds foundation** - Everything built properly from start
4. ✅ **Manageable risk** - Can stop if not working
5. ✅ **Realistic timeline** - Fits your 2 days/week capacity
6. ✅ **Affordable** - £15k is defensible for clear deliverable

**Then** if successful, proceed to Option 2 (Leasing focus) where real transformation happens.

---

### Immediate Next Steps:

1. **Present this proposal to decision maker** (This week)
   - Focus on Option 1 with Option 2 as "if successful"
   - Highlight ROI and quick payback

2. **If approved, schedule kick-off** (Week 1)
   - Confirm scope
   - Access to data/systems
   - Set up governance

3. **Discovery phase** (Week 1-2)
   - Analyze current spreadsheet
   - Interview key users
   - Finalize data model

4. **Development begins** (Week 3)
   - You're already ahead with working prototype!

---

## Questions to Answer Before Presenting

### For You to Decide:
1. What hourly rate do you want to charge?
   - Option 1 calculations: £78/hour (competitive for UK contractor)
   - Could go lower (£50-60/hour) if you want to be more conservative
   - Could position as fixed price (£15k) to remove hourly discussion

2. Do you want to be positioned as:
   - Internal employee doing extra project?
   - External consultant/contractor?
   - (Affects taxes, contracts, liability)

3. Are you comfortable with ongoing support commitment?
   - Or just build-and-handover?

### For Them to Answer:
1. Who's the actual decision maker?
2. What's budget approval process?
3. Timeline expectations (urgent or can wait)?
4. What happens if you leave/unavailable?

---

## Alternative Pricing Models

### Model 1: Fixed Price (Recommended for Board)
- **Option 1**: £15,000 fixed (what I calculated)
- **Option 2**: £28,000 fixed
- **Option 3**: £50,000 fixed

**Advantage**: Simple, no surprises, easy to approve  
**Risk**: If scope creeps, you're stuck

### Model 2: Time & Materials
- **Hourly rate**: £60-80/hour
- **Monthly cap**: £5,000-7,000
- **Invoice monthly** for actual hours

**Advantage**: Flexible, fair for both sides  
**Risk**: Harder to get approved, unpredictable cost

### Model 3: Retainer + Deliverables
- **Monthly retainer**: £3,000/month (covers your 2 days/week)
- **Milestone bonuses**: £2,000-3,000 per major deliverable
- **Duration**: 3-15 months depending on scope

**Advantage**: Steady income for you, predictable for them  
**Risk**: Needs clear deliverable definitions

---

## My Honest Assessment

**Can you deliver Option 1 in 3 months at 2 days/week?**  
✅ **Yes** - You already have working prototype. This is realistic.

**Can you deliver Option 2 in 6 months?**  
✅ **Probably** - Depends on Agency Pilot integration complexity.

**Can you deliver Option 3 in 12-15 months solo?**  
⚠️ **Challenging** - Doable but ambitious for one person. May need 18 months or help.

**Should you present all three options?**  
✅ **Yes** - Shows vision, but recommend Option 1 strongly.

**What's biggest risk?**  
⚠️ **Your availability** - What if you get sick, leave company, or priorities change?  
💡 **Mitigation**: Build everything well-documented, use standard technologies, consider handover plan.

---

## Final Thought

**This is a great opportunity** to solve real problems and build something meaningful. The spreadsheet pain is real, the ROI is clear, and you have working code already.

**Start small (Option 1)**, prove value, then grow. Don't promise the moon upfront.

**Position it as**: *"Let's solve the weekly report problem properly, build it on a solid foundation, and if it works well, we can expand it to help other departments too."*

That's an easy sell.

---

**Ready to refine this proposal together?** I can help you:
- Adjust pricing
- Create presentation slides
- Draft formal contract
- Plan the discovery phase
- Design the data model

Let me know what you need!
