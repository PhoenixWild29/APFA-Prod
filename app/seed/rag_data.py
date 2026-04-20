"""RAG seed data — real financial advisory content for the APFA knowledge base.

Creates the MinIO bucket and populates a DeltaTable with foundational
financial documents covering lending regulations, mortgage guidance,
loan eligibility, personal finance best practices, and risk assessment.

Usage:
    # From within the container (or lifespan auto-seeds on first boot):
    python -m app.seed.rag_data
"""

import logging
import uuid
from datetime import date

import pandas as pd
from minio import Minio

logger = logging.getLogger(__name__)

BUCKET_NAME = "customer-data-lakehouse"

# Each document is a self-contained passage of real financial content.
# chunk_id == document_id for seed data; future chunking will produce
# multiple chunk_ids per document_id.
DOCUMENTS = [
    {
        "document_type": "regulation",
        "source": "CFPB",
        "filename": "tila_truth_in_lending_act.txt",
        "profile": (
            "The Truth in Lending Act (TILA) requires lenders to disclose the "
            "total cost of credit to consumers before they enter into a loan "
            "agreement. Key disclosures include the annual percentage rate (APR), "
            "total finance charges, the total amount financed, and the total of "
            "all payments over the life of the loan. TILA applies to most consumer "
            "credit transactions including mortgages, auto loans, credit cards, "
            "and home equity lines of credit. Lenders must provide a Loan Estimate "
            "within three business days of receiving a mortgage application and a "
            "Closing Disclosure at least three business days before closing. "
            "Violations of TILA can result in statutory damages, actual damages, "
            "and attorney fees. The right of rescission allows borrowers to cancel "
            "certain home-secured loans within three days of closing."
        ),
    },
    {
        "document_type": "regulation",
        "source": "CFPB",
        "filename": "respa_real_estate_settlement.txt",
        "profile": (
            "The Real Estate Settlement Procedures Act (RESPA) protects consumers "
            "during the home buying and mortgage process by requiring transparency "
            "in settlement costs. RESPA prohibits kickbacks and unearned fees "
            "between settlement service providers, requires lenders to provide "
            "borrowers with a Good Faith Estimate of settlement costs, and mandates "
            "disclosure of the servicing relationship. Under RESPA, lenders cannot "
            "require borrowers to use a particular title insurance company, and "
            "must provide an annual escrow account statement. The law also limits "
            "the amount lenders can hold in escrow accounts to cover taxes and "
            "insurance. Servicers must respond to qualified written requests "
            "within 30 business days and cannot charge fees during the response "
            "period. RESPA violations can result in fines up to $10,000 per "
            "violation and up to one year imprisonment for pattern violations."
        ),
    },
    {
        "document_type": "regulation",
        "source": "Federal Reserve",
        "filename": "ecoa_equal_credit_opportunity.txt",
        "profile": (
            "The Equal Credit Opportunity Act (ECOA) prohibits discrimination in "
            "any aspect of a credit transaction based on race, color, religion, "
            "national origin, sex, marital status, age, receipt of public "
            "assistance income, or good faith exercise of rights under the "
            "Consumer Credit Protection Act. Lenders must evaluate creditworthiness "
            "based on objective criteria such as income, expenses, debts, and "
            "credit history. When a lender denies credit or offers less favorable "
            "terms, they must provide an adverse action notice within 30 days "
            "explaining the specific reasons for the decision or informing the "
            "applicant of their right to request those reasons. ECOA also requires "
            "lenders to consider income from part-time employment, pensions, and "
            "annuities without discrimination. Married applicants have the right "
            "to open credit accounts in their own name."
        ),
    },
    {
        "document_type": "regulation",
        "source": "Federal Reserve",
        "filename": "fair_lending_act.txt",
        "profile": (
            "The Fair Housing Act prohibits discrimination in residential real "
            "estate transactions including mortgage lending, appraisals, and "
            "mortgage insurance. Protected classes include race, color, national "
            "origin, religion, sex, familial status, and disability. Lenders must "
            "not engage in redlining (refusing to lend in certain neighborhoods), "
            "steering (directing borrowers toward less favorable loan products), "
            "or disparate pricing (charging higher rates to protected classes). "
            "The Community Reinvestment Act (CRA) further requires banks to meet "
            "the credit needs of all segments of their communities, including "
            "low- and moderate-income neighborhoods. Federal regulators conduct "
            "fair lending examinations and use statistical analysis of HMDA data "
            "to identify potential discriminatory patterns. Penalties for fair "
            "lending violations include civil money penalties, restitution to "
            "affected borrowers, and injunctive relief."
        ),
    },
    {
        "document_type": "guideline",
        "source": "Mortgage Industry Standards",
        "filename": "fixed_vs_adjustable_rate.txt",
        "profile": (
            "Fixed-rate mortgages maintain the same interest rate for the entire "
            "loan term, providing payment predictability. Common terms are 15-year "
            "and 30-year, with 15-year loans carrying lower rates but higher "
            "monthly payments. Adjustable-rate mortgages (ARMs) start with a lower "
            "introductory rate that adjusts periodically based on a benchmark "
            "index plus a margin. A 5/1 ARM has a fixed rate for five years, then "
            "adjusts annually. ARMs include rate caps: initial adjustment cap "
            "(typically 2%), periodic adjustment cap (usually 2%), and lifetime "
            "cap (commonly 5-6% above the initial rate). Borrowers should consider "
            "an ARM if they plan to sell or refinance before the adjustment period, "
            "have rising income expectations, or when fixed rates are significantly "
            "higher. The fully indexed rate (index + margin) indicates what the "
            "rate could adjust to. Payment shock occurs when ARM rates reset "
            "significantly higher, increasing monthly payments by hundreds of "
            "dollars."
        ),
    },
    {
        "document_type": "guideline",
        "source": "Mortgage Industry Standards",
        "filename": "apr_vs_interest_rate.txt",
        "profile": (
            "The annual percentage rate (APR) and the interest rate are related "
            "but distinct concepts. The interest rate is the cost of borrowing "
            "the principal amount, expressed as a percentage. The APR is a broader "
            "measure that includes the interest rate plus other costs such as "
            "origination fees, discount points, mortgage insurance premiums, and "
            "certain closing costs, annualized over the loan term. For example, "
            "a mortgage with a 6.5% interest rate might have a 6.8% APR after "
            "accounting for fees. The APR enables borrowers to compare loan offers "
            "on an apples-to-apples basis because it captures the true total cost "
            "of financing. However, APR has limitations: it assumes the borrower "
            "keeps the loan for the full term, and it does not account for "
            "prepayment or refinancing. When comparing loans, borrowers should "
            "examine both the rate and APR, as a loan with a lower rate but higher "
            "fees may have a higher APR than a loan with a slightly higher rate "
            "and lower fees."
        ),
    },
    {
        "document_type": "guideline",
        "source": "Mortgage Industry Standards",
        "filename": "rate_lock_periods.txt",
        "profile": (
            "A rate lock is a commitment from a lender to hold a specific interest "
            "rate and points for a borrower for a defined period, typically 30 to "
            "60 days, while the loan application is processed. Longer lock periods "
            "(90-120 days) are available but usually come with a slightly higher "
            "rate or additional fees because the lender bears more interest rate "
            "risk. If rates drop during the lock period, borrowers may not benefit "
            "unless they have a float-down option, which allows a one-time rate "
            "reduction if market rates decline by a specified threshold (commonly "
            "0.25-0.5%). If the lock expires before closing, borrowers may need to "
            "pay for a rate lock extension or accept current market rates. Best "
            "practices include locking the rate after receiving a satisfactory "
            "Loan Estimate, confirming the lock terms in writing, and ensuring the "
            "lock period covers the expected closing timeline with a buffer for "
            "potential delays."
        ),
    },
    {
        "document_type": "eligibility",
        "source": "FHA/HUD",
        "filename": "fha_loan_requirements.txt",
        "profile": (
            "FHA loans are government-insured mortgages designed for borrowers who "
            "may not qualify for conventional financing. Minimum requirements "
            "include a credit score of 580 for 3.5% down payment (or 500-579 with "
            "10% down), a debt-to-income ratio not exceeding 43% (though exceptions "
            "exist up to 50% with compensating factors), and steady employment "
            "history for at least two years. FHA loans require mortgage insurance "
            "premiums (MIP): an upfront premium of 1.75% of the loan amount "
            "(financed into the loan) and annual premiums of 0.45-1.05% depending "
            "on the loan term, amount, and LTV ratio. For loans with less than 10% "
            "down, MIP is required for the life of the loan. FHA loan limits vary "
            "by county, ranging from $472,030 in standard areas to $1,089,300 in "
            "high-cost areas. The property must be the borrower's primary "
            "residence and meet FHA minimum property standards."
        ),
    },
    {
        "document_type": "eligibility",
        "source": "VA",
        "filename": "va_loan_requirements.txt",
        "profile": (
            "VA loans are available to eligible veterans, active-duty service "
            "members, and surviving spouses. Key benefits include no down payment "
            "requirement, no private mortgage insurance (PMI), competitive interest "
            "rates, and limited closing costs. Eligibility requires a Certificate "
            "of Eligibility (COE) based on service history: 90 consecutive days of "
            "active service during wartime, 181 days during peacetime, or 6 years "
            "in the National Guard or Reserves. VA loans have no maximum loan "
            "amount for borrowers with full entitlement, though lenders may impose "
            "their own limits. A VA funding fee (1.25-3.3% of the loan amount) "
            "replaces PMI and can be financed into the loan; disabled veterans are "
            "exempt. The VA requires a property appraisal to meet Minimum Property "
            "Requirements (MPRs) ensuring the home is safe, structurally sound, "
            "and sanitary. VA loans can be used for purchase, refinance (IRRRL "
            "streamline or cash-out), and construction."
        ),
    },
    {
        "document_type": "eligibility",
        "source": "Fannie Mae / Freddie Mac",
        "filename": "conventional_loan_requirements.txt",
        "profile": (
            "Conventional loans are mortgages not insured by a government agency. "
            "Conforming conventional loans meet Fannie Mae and Freddie Mac "
            "guidelines with loan limits of $766,550 in most areas (2024) and up "
            "to $1,149,825 in high-cost areas. Minimum credit score requirements "
            "are typically 620, though rates improve significantly at 740 and "
            "above. Down payment minimums are 3% for first-time buyers (with PMI) "
            "and 5% for repeat buyers. Private mortgage insurance (PMI) is required "
            "when the down payment is less than 20% and costs 0.3-1.5% of the loan "
            "amount annually; it can be cancelled when equity reaches 20%. "
            "Debt-to-income ratio limits are generally 36-45%, with the housing "
            "payment (PITI) not exceeding 28% of gross monthly income. Jumbo loans "
            "exceed conforming limits and typically require 10-20% down, 700+ "
            "credit score, and 36% DTI maximum. Cash reserves of 2-12 months of "
            "payments may be required depending on loan size."
        ),
    },
    {
        "document_type": "eligibility",
        "source": "APFA Advisory",
        "filename": "dti_ratio_explained.txt",
        "profile": (
            "The debt-to-income (DTI) ratio is a critical underwriting metric that "
            "measures the percentage of a borrower's gross monthly income that goes "
            "toward debt payments. Front-end DTI (housing ratio) includes only "
            "housing costs: mortgage principal, interest, taxes, insurance, HOA "
            "fees, and PMI. Back-end DTI includes all monthly debt obligations: "
            "housing costs plus car loans, student loans, credit card minimum "
            "payments, personal loans, and child support. Conventional loans "
            "generally require a front-end DTI of 28% or less and a back-end DTI "
            "of 36-43%. FHA loans allow back-end DTI up to 43% (or 50% with "
            "compensating factors). To calculate DTI: sum all monthly debt payments "
            "and divide by gross monthly income. For example, a borrower earning "
            "$8,000/month with a $2,000 mortgage, $400 car payment, and $200 "
            "student loan has a back-end DTI of 32.5%. Strategies to improve DTI "
            "include paying down revolving debt, avoiding new debt before "
            "application, and increasing income documentation."
        ),
    },
    {
        "document_type": "eligibility",
        "source": "APFA Advisory",
        "filename": "credit_score_tiers.txt",
        "profile": (
            "Credit scores significantly impact mortgage terms and eligibility. "
            "FICO scores range from 300 to 850 and are categorized into tiers: "
            "Exceptional (800-850) qualifies for the best rates and terms with "
            "minimal documentation requirements. Very Good (740-799) receives "
            "near-best rates and broad program eligibility. Good (670-739) "
            "qualifies for most conventional programs but at slightly higher rates. "
            "Fair (580-669) limits options primarily to FHA loans; conventional "
            "loans may require larger down payments and higher PMI. Poor (below "
            "580) restricts options to FHA with 10% down, portfolio lenders, or "
            "subprime products with significantly higher rates. Factors affecting "
            "FICO scores: payment history (35%), amounts owed/utilization (30%), "
            "length of credit history (15%), credit mix (10%), and new credit "
            "inquiries (10%). To improve scores before a mortgage application: "
            "pay all bills on time, reduce credit card utilization below 30%, "
            "avoid opening new accounts, dispute errors on credit reports, and "
            "maintain old accounts for credit history length."
        ),
    },
    {
        "document_type": "best_practice",
        "source": "APFA Advisory",
        "filename": "emergency_fund_sizing.txt",
        "profile": (
            "An emergency fund is a liquid savings reserve to cover unexpected "
            "expenses without resorting to debt. The standard recommendation is "
            "3-6 months of essential living expenses, but the appropriate amount "
            "depends on individual circumstances. Single-income households, "
            "self-employed individuals, and those in volatile industries should "
            "target 6-12 months. Dual-income households with stable employment "
            "may be adequately covered with 3-4 months. Essential expenses to "
            "calculate include housing (mortgage or rent, utilities, insurance), "
            "food, transportation, minimum debt payments, healthcare premiums, "
            "and any dependent care costs. The fund should be kept in a high-yield "
            "savings account or money market account — accessible within 1-2 "
            "business days but separate from daily checking to avoid temptation. "
            "Building the fund incrementally through automatic transfers of 10-20% "
            "of take-home pay is more sustainable than trying to save a lump sum. "
            "The emergency fund should be fully funded before aggressive investing "
            "or extra debt payments."
        ),
    },
    {
        "document_type": "best_practice",
        "source": "APFA Advisory",
        "filename": "50_30_20_budgeting.txt",
        "profile": (
            "The 50/30/20 budgeting framework allocates after-tax income into "
            "three categories. Needs (50%): housing, utilities, groceries, minimum "
            "debt payments, insurance premiums, transportation, and childcare — "
            "essential expenses that cannot be easily eliminated. Wants (30%): "
            "dining out, entertainment, subscriptions, hobbies, vacations, and "
            "non-essential shopping — spending that improves quality of life but "
            "is discretionary. Savings and debt repayment (20%): emergency fund "
            "contributions, retirement savings (401k, IRA), extra debt payments "
            "above minimums, and investment contributions. For high-cost-of-living "
            "areas where housing alone exceeds 30% of income, a modified 60/20/20 "
            "or 70/15/15 split may be more realistic. The framework works best as "
            "a starting point that individuals adjust based on their financial "
            "goals. Someone aggressively paying off student loans might use "
            "50/20/30 (allocating more to debt payoff), while someone saving for "
            "a home down payment might temporarily shift to 50/15/35."
        ),
    },
    {
        "document_type": "best_practice",
        "source": "APFA Advisory",
        "filename": "debt_payoff_strategies.txt",
        "profile": (
            "Two primary strategies exist for paying off multiple debts. The "
            "avalanche method targets the highest-interest debt first while making "
            "minimum payments on all others. This minimizes total interest paid "
            "and is mathematically optimal. For example, paying off a 22% credit "
            "card before a 6% student loan saves significantly more in interest. "
            "The snowball method targets the smallest balance first regardless of "
            "interest rate, providing psychological wins that build momentum. "
            "Research shows the snowball method has higher completion rates because "
            "of the motivational effect of eliminating individual debts. A hybrid "
            "approach works well: use the avalanche method but if two debts have "
            "similar interest rates, pay the smaller one first. Debt consolidation "
            "combines multiple debts into a single payment, ideally at a lower "
            "rate, through personal loans or balance transfer credit cards (often "
            "0% APR for 12-21 months). Refinancing high-interest debt to a lower "
            "rate through a home equity loan or HELOC can reduce costs but "
            "converts unsecured debt to secured debt backed by the home."
        ),
    },
    {
        "document_type": "best_practice",
        "source": "APFA Advisory",
        "filename": "retirement_savings_fundamentals.txt",
        "profile": (
            "Retirement savings should begin as early as possible to maximize "
            "compound growth. Employer-sponsored 401(k) plans should be funded "
            "at least to the employer match level — not capturing the full match "
            "is leaving free money on the table. For 2024, 401(k) contribution "
            "limits are $23,000 ($30,500 for those 50 and older). Traditional "
            "401(k) contributions reduce taxable income in the current year but "
            "are taxed upon withdrawal in retirement. Roth 401(k) contributions "
            "are made after-tax but grow and are withdrawn tax-free. The choice "
            "depends on whether you expect higher or lower tax rates in retirement. "
            "Individual Retirement Accounts (IRAs) provide additional savings "
            "capacity: $7,000 per year ($8,000 if 50+). A common sequence is: "
            "(1) 401(k) up to employer match, (2) max out Roth IRA, (3) max out "
            "remaining 401(k), (4) taxable brokerage account. Target savings rate "
            "for retirement is 15-20% of gross income including employer "
            "contributions. The 4% rule suggests that a retiree can withdraw 4% "
            "of their portfolio annually with minimal risk of running out."
        ),
    },
    {
        "document_type": "risk_assessment",
        "source": "APFA Advisory",
        "filename": "credit_risk_factors.txt",
        "profile": (
            "Credit risk assessment evaluates the likelihood that a borrower will "
            "default on their obligations. The five Cs of credit provide a "
            "framework: Character (credit history, payment patterns, and "
            "willingness to repay), Capacity (income adequacy and stability to "
            "service debt, measured by DTI ratio), Capital (assets and net worth "
            "that provide a financial cushion), Collateral (property or assets "
            "pledged to secure the loan), and Conditions (economic environment, "
            "industry trends, and loan purpose). Quantitative risk metrics include "
            "probability of default (PD), loss given default (LGD), and exposure "
            "at default (EAD). Expected loss = PD x LGD x EAD. Lenders use credit "
            "scoring models, income verification, employment history (minimum two "
            "years preferred), and asset documentation to assess risk. Red flags "
            "include frequent job changes, declining income trends, high credit "
            "utilization, recent delinquencies, and large unexplained deposits. "
            "Risk-based pricing adjusts interest rates and terms based on the "
            "assessed credit risk of each borrower."
        ),
    },
    {
        "document_type": "risk_assessment",
        "source": "APFA Advisory",
        "filename": "loan_to_value_ratios.txt",
        "profile": (
            "The loan-to-value (LTV) ratio is the mortgage amount divided by the "
            "appraised property value, expressed as a percentage. An LTV of 80% "
            "means the borrower is putting 20% down. LTV directly impacts mortgage "
            "insurance requirements, interest rates, and loan approval. Conventional "
            "loans with LTV above 80% require private mortgage insurance (PMI) at "
            "0.3-1.5% of the loan amount annually. PMI can be cancelled when LTV "
            "reaches 80% through payments or appreciation; it automatically "
            "terminates at 78% of original value. Combined LTV (CLTV) includes "
            "all liens against the property — a first mortgage at 80% LTV plus a "
            "home equity line at 10% results in a 90% CLTV. FHA loans require "
            "MIP regardless of LTV (though terms vary). VA loans allow 100% LTV "
            "with no mortgage insurance. For refinancing, LTV affects available "
            "programs: rate-term refinance typically allows up to 95-97% LTV, "
            "while cash-out refinance is generally limited to 80% LTV for "
            "conventional and 90% for VA."
        ),
    },
    {
        "document_type": "risk_assessment",
        "source": "APFA Advisory",
        "filename": "underwriting_criteria.txt",
        "profile": (
            "Mortgage underwriting is the process of evaluating a borrower's "
            "financial profile to determine loan approval. Automated underwriting "
            "systems (AUS) like Fannie Mae's Desktop Underwriter (DU) and Freddie "
            "Mac's Loan Product Advisor (LPA) provide preliminary decisions based "
            "on credit data, income, assets, and property information. Common "
            "underwriting requirements include: two years of tax returns and W-2s, "
            "30 days of pay stubs, two months of bank statements, explanation "
            "letters for large deposits or credit inquiries, and a property "
            "appraisal. Self-employed borrowers typically need two years of "
            "business tax returns and a year-to-date profit and loss statement. "
            "Gift funds for down payment are allowed but must be documented with "
            "a gift letter and transfer evidence. Underwriters verify employment "
            "directly with employers before closing. Common conditions that delay "
            "or prevent approval include undisclosed debts discovered on updated "
            "credit reports, appraisal shortfalls requiring renegotiation, and "
            "employment changes during the loan process."
        ),
    },
    {
        "document_type": "best_practice",
        "source": "APFA Advisory",
        "filename": "homebuying_readiness_checklist.txt",
        "profile": (
            "Before applying for a mortgage, prospective homebuyers should "
            "complete a financial readiness assessment. Check credit reports from "
            "all three bureaus (Equifax, Experian, TransUnion) at annualcreditreport.com "
            "and dispute any errors at least 3-6 months before applying. Save for "
            "a down payment: 20% avoids PMI on conventional loans, but 3-5% is "
            "sufficient with PMI. Budget for closing costs (2-5% of the purchase "
            "price) and moving expenses separately from the down payment. Build "
            "2-3 months of cash reserves after down payment and closing costs. "
            "Avoid major purchases, new credit applications, or job changes in the "
            "6 months before applying. Get pre-approved (not just pre-qualified) "
            "to understand your actual borrowing capacity and show sellers you are "
            "a serious buyer. Calculate your comfortable monthly payment using the "
            "28% rule: housing costs should not exceed 28% of gross monthly income. "
            "Factor in property taxes, homeowner's insurance, HOA fees, and "
            "maintenance reserves (1-2% of home value annually) beyond the "
            "mortgage payment itself."
        ),
    },
]


def seed_rag_data() -> None:
    """Create the MinIO bucket and populate the DeltaTable with seed data.

    Idempotent: if the DeltaTable already has rows, skip seeding entirely.
    This prevents wiping connector-ingested data on deploy/restart.

    Only seeds on first boot (empty or missing table).
    Uses DELTA_SCHEMA for type-safe Arrow writes.
    """
    import deltalake

    from app.config import settings
    from app.connectors.base import get_delta_schema
    from app.services.delta_writer import _conform_df_to_schema
    from app.storage import get_delta_storage_options

    # 1. Ensure MinIO bucket exists
    mc = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=False,
    )
    if not mc.bucket_exists(BUCKET_NAME):
        mc.make_bucket(BUCKET_NAME)
        logger.info(f"Created MinIO bucket: {BUCKET_NAME}")
    else:
        logger.info(f"MinIO bucket already exists: {BUCKET_NAME}")

    storage_options = get_delta_storage_options()

    # 2. Check if table already has data — if so, skip seed
    try:
        dt = deltalake.DeltaTable(
            settings.delta_table_path, storage_options=storage_options
        )
        existing = dt.to_pandas()
        if len(existing) > 0:
            logger.info(
                f"DeltaTable has {len(existing)} rows — skipping seed "
                f"(connector data preserved)"
            )
            return
    except Exception:
        pass  # Table doesn't exist yet — proceed with seed

    # 3. Build DataFrame with all DELTA_SCHEMA columns
    rows = []
    for doc in DOCUMENTS:
        doc_id = str(uuid.uuid4())
        rows.append(
            {
                "document_id": doc_id,
                "chunk_id": doc_id,
                "filename": doc["filename"],
                "document_type": doc["document_type"],
                "source": doc["source"],
                "creation_date": str(date.today()),
                "file_size_bytes": len(doc["profile"].encode("utf-8")),
                "profile": doc["profile"],
                # Pipeline columns — null for seed data
                "external_id": f"seed:{doc_id}",
                "source_connector": "seed",
                "source_url": "",
                "parent_document_id": doc_id,
                "chunk_index": 0,
                "total_chunks": 1,
                "ingested_at": "",
                "ttl_hours": None,
                "freshness_class": "static",
                "content_kind": doc["document_type"],
                "metadata_json": "{}",
                # Embedding columns — null, filled by load_rag_index on first boot
                "embedding_vector": None,
                "embedding_model": None,
                "content_hash": None,
                "embedded_at": None,
            }
        )

    df = pd.DataFrame(rows)

    # 4. Convert to Arrow with explicit DELTA_SCHEMA
    schema = get_delta_schema()
    conformed = _conform_df_to_schema(df, schema)
    import pyarrow as pa

    table = pa.Table.from_pandas(conformed, schema=schema, preserve_index=False)

    # 5. Write DeltaTable — mode="overwrite" is safe here since we verified
    #    the table was empty or missing above
    deltalake.write_deltalake(
        settings.delta_table_path,
        table,
        mode="overwrite",
        storage_options=storage_options,
    )
    logger.info(
        f"RAG seed complete: {len(rows)} documents written to "
        f"{settings.delta_table_path}"
    )

    # 6. Verify the write
    dt = deltalake.DeltaTable(
        settings.delta_table_path, storage_options=storage_options
    )
    verify_df = dt.to_pandas()
    logger.info(f"Verification: DeltaTable has {len(verify_df)} rows")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_rag_data()
