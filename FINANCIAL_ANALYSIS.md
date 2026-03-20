# SaaS Financial Analysis - Assumptions & Interpretation

## Executive Summary

This document provides a comprehensive explanation of the assumptions and methodology used in the BahnSetu SaaS Financial Simulation Model, along with interpretation of key results.

---

## 1. Model Assumptions

### 1.1 Customer Acquisition & Growth

| Parameter | Default Value | Assumption |
|-----------|---------------|------------|
| Starting Customers | 50 | Initial customer base representing early-stage SaaS company |
| Monthly Growth Rate | 20% | Assumes strong product-market fit with aggressive customer acquisition |
| Growth Model | Compound monthly | New customers = Current customers × Growth rate |

### 1.2 Customer Churn

| Parameter | Default Value | Assumption |
|-----------|---------------|------------|
| Base Churn Rate | 5% monthly | Industry standard for SMB SaaS (3-7% typical) |
| High Churn Scenario | 10% monthly | Stressed scenario for risk analysis |
| Churn Impact | Applied to start-of-month customers | Churned customers × Price = Churn MRR impact |

### 1.3 Pricing & Revenue

| Parameter | Default Value | Assumption |
|-----------|---------------|------------|
| Average Price | $100/month | Blended average across pricing tiers |
| Pricing Tiers | Basic ($49), Pro ($99), Enterprise ($299) | Tier split: 50%, 35%, 15% |
| Expansion Revenue | 2% of base customers upgrading 20% | Represents account expansion/Upsell |

### 1.4 Cost Structure

| Parameter | Default Value | Assumption |
|-----------|---------------|------------|
| Fixed Costs | $5,000/month | G&A overhead, office, admin |
| Variable Cost/Customer | $10/month | COGS, hosting, support per customer |
| Customer Acquisition Cost (CAC) | $150 | Marketing & sales spend per new customer |

### 1.5 Operational Costs

| Department | Headcount | Monthly Salary | Hiring Threshold |
|------------|------------|----------------|------------------|
| Engineering | 5 (initial) | $8,500 | +1 per 30 customers |
| Sales | 3 (initial) | $6,000 | +1 per 20 customers |
| Marketing | 2 (initial) | $5,500 | +1 per 25 customers |
| Customer Success | 2 (initial) | $4,500 | +1 per 35 customers |
| G&A | 2 (initial) | $5,000 | +1 per 50 customers |

---

## 2. Key Metrics Explained

### 2.1 MRR (Monthly Recurring Revenue)
- **Formula**: Sum of all customer tier revenues
- **Interpretation**: Core revenue metric; should show consistent MoM growth in healthy scenarios

### 2.2 ARR (Annual Recurring Revenue)
- **Formula**: MRR × 12
- **Interpretation**: Standardized annual revenue figure for valuation comparisons

### 2.3 LTV (Lifetime Value)
- **Formula**: (Price - Variable Cost) / Churn Rate
- **Benchmark**: LTV:CAC ratio should exceed 3:1 for sustainable growth
- **Example**: ($100 - $10) / 0.05 = $1,800 LTV

### 2.4 CAC Payback Period
- **Formula**: CAC / (Price - Variable Cost)
- **Benchmark**: Should be < 12 months for healthy SaaS
- **Example**: $150 / $90 = 1.67 months

### 2.5 Gross Margin
- **Formula**: (Revenue - COGS) / Revenue × 100
- **Benchmark**: 70%+ indicates scalable SaaS model
- **Current**: ~90% due to low variable costs

### 2.6 S&M Efficiency
- **Formula**: Net New MRR / Sales & Marketing Cost
- **Benchmark**: >1.0 indicates efficient customer acquisition
- **Interpretation**: Values above 1.0 mean each $1 spent generates >$1 MRR

### 2.7 LTV:CAC Ratio
- **Formula**: LTV / CAC
- **Benchmark**: >3:1 is considered healthy
- **Interpretation**: Higher ratio = better unit economics

---

## 3. Interpretation of Results

### 3.1 Base Case Scenario (5% Churn)

**Key Observations:**
- **MRR Growth**: Shows consistent month-over-month growth from ~$6,000 to ~$153,000 over 24 months
- **Customer Growth**: Starts at 50 customers, grows to ~1,471 by month 24
- **Gross Margin**: Stable at ~90% due to low variable costs
- **Break-even**: Not achieved within 24 months (cumulative cash remains negative)
- **LTV:CAC**: ~12x indicates excellent unit economics

**Why Break-even is Not Achieved:**
- High headcount costs (Engineering team dominates)
- Customer acquisition costs ongoing
- 24-month period too short for break-even at this growth rate

### 3.2 High Churn Scenario (10% Churn)

**Key Observations:**
- **MRR Growth**: Slower growth, reaching ~$51,655 by month 24
- **Customer Growth**: Starts at 50, grows to ~495 by month 24 (vs 1,471 in base)
- **LTV:CAC**: ~6x (vs 12x in base) - still healthy but half the efficiency
- **Cumulative Cash**: Worse position due to lower revenue

**Impact of High Churn:**
- Churn directly reduces customer base
- Each churned customer represents lost LTV
- Higher churn requires faster acquisition to maintain growth

---

## 4. Sensitivity Analysis

### 4.1 Growth Rate Impact
| Growth Rate | Final MRR (24mo) | Final Customers | Cumulative Cash |
|-------------|------------------|----------------|----------------|
| 10% | ~$30,000 | ~400 | ~-$9M |
| 20% | ~$153,000 | ~1,471 | ~-$7.3M |
| 30% | ~$520,000 | ~4,000+ | ~-$5M |

### 4.2 Churn Rate Impact
| Churn Rate | Final MRR (24mo) | Final Customers | LTV:CAC |
|------------|------------------|----------------|---------|
| 3% | ~$175,000 | ~1,700 | ~20x |
| 5% | ~$153,000 | ~1,471 | ~12x |
| 10% | ~$51,000 | ~495 | ~6x |
| 15% | ~$12,000 | ~180 | ~3x |

### 4.3 Price Sensitivity
| Price Point | Final MRR (24mo) | Gross Margin % | LTV |
|-------------|------------------|---------------|-----|
| $50 | ~$76,000 | ~80% | $800 |
| $100 | ~$153,000 | ~90% | $1,800 |
| $200 | ~$306,000 | ~95% | $3,800 |

---

## 5. Recommendations

### 5.1 Break-even Strategy
1. **Reduce headcount growth** - Consider delayed hiring
2. **Increase pricing** - Enterprise tier has best unit economics
3. **Reduce CAC** - Improve marketing efficiency
4. **Extend timeline** - 36-48 months for realistic break-even

### 5.2 Churn Mitigation
1. **Improve customer success** - Early engagement reduces churn
2. **Monitor leading indicators** - Usage patterns predict churn
3. **Implement retention programs** - Onboarding, education, incentives

### 5.3 Growth Optimization
1. **Focus on enterprise** - Higher LTV, lower churn
2. **Improve S&M efficiency** - Target >1.5x ratio
3. **Optimize pricing tiers** - Balance between ARPU and conversion

---

## 6. Limitations & Future Improvements

### Current Limitations:
1. **No seasonality modeling** - Revenue may fluctuate seasonally
2. **Simplified headcount model** - Real hiring has delays and costs
3. **No geographic pricing** - Single market assumption
4. **Deterministic model** - No stochastic elements for risk analysis

### Suggested Enhancements:
1. Add Monte Carlo simulation for risk quantification
2. Include seasonality factors
3. Add geographic/market segmentation
4. Include cohort analysis
5. Add capex and funding runway modeling

---

## 7. Conclusion

The BahnSetu SaaS Financial Model provides a robust framework for understanding the financial dynamics of a SaaS business. Key takeaways:

1. **Unit economics are strong** - LTV:CAC ratio exceeds benchmarks
2. **Break-even requires patience** - 24 months insufficient at current growth rate
3. **Churn is critical** - 2x churn rate halves final customer base
4. **Scale favors the model** - Larger customer base improves all metrics

The model supports decision-making for:
- Pricing strategy adjustments
- Customer acquisition investment decisions
- Cost structure optimization
- Scenario planning and risk assessment

---

*Document Version: 1.0*  
*Last Updated: March 2026*  
*Model Version: BahnSetu SaaS Simulator v2.0*
