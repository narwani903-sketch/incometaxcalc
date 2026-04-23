import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Income Tax Calculator FY 2025-26", layout="wide")

st.title("💰 Income Tax Calculator (FY 2025-26 / AY 2026-27)")
st.write("Default Tax Regime with Rebate, Marginal Relief, Surcharge & Agriculture Income")

# -------------------------
# INPUTS
# -------------------------
st.sidebar.header("📥 Enter Income Details")

salary = st.sidebar.number_input("Salary Income", 0.0)
house_property = st.sidebar.number_input("House Property Income", 0.0)
business = st.sidebar.number_input("Business/Profession Income", 0.0)
capital_gains = st.sidebar.number_input("Capital Gains", 0.0)
other_sources = st.sidebar.number_input("Other Sources", 0.0)
agri_income = st.sidebar.number_input("Agriculture Income (for rate purpose)", 0.0)

# -------------------------
# STANDARD DEDUCTION (ONLY SALARY)
# -------------------------
std_deduction = min(75000, salary)
salary_net = salary - std_deduction

# -------------------------
# GROSS TOTAL INCOME
# -------------------------
gross_total_income = (
    salary_net +
    house_property +
    business +
    capital_gains +
    other_sources
)

taxable_income = max(0, gross_total_income)

# -------------------------
# TAX SLAB FUNCTION (NEW REGIME)
# -------------------------
def slab_tax(income):
    slabs = [
        (400000, 0),
        (800000, 0.05),
        (1200000, 0.10),
        (1600000, 0.15),
        (2000000, 0.20),
        (2400000, 0.25),
        (float('inf'), 0.30)
    ]

    tax = 0
    prev = 0

    for limit, rate in slabs:
        if income > prev:
            taxable = min(income, limit) - prev
            tax += taxable * rate
            prev = limit
        else:
            break

    return tax

# -------------------------
# AGRICULTURE INCOME (PARTIAL INTEGRATION)
# -------------------------
def agri_tax(income, agri):
    if agri <= 5000:
        return slab_tax(income)

    tax1 = slab_tax(income + agri)
    tax2 = slab_tax(agri + 400000)
    return tax1 - tax2

tax_before_rebate = agri_tax(taxable_income, agri_income)

# -------------------------
# REBATE u/s 87A
# -------------------------
rebate = 0
if taxable_income <= 1200000:
    rebate = min(tax_before_rebate, 60000)

tax_after_rebate = tax_before_rebate - rebate

# -------------------------
# MARGINAL RELIEF (REBATE CLIFF @ 12L)
# -------------------------
if taxable_income > 1200000:
    excess_income = taxable_income - 1200000
    max_tax = excess_income
    if tax_after_rebate > max_tax:
        tax_after_rebate = max_tax

# -------------------------
# SURCHARGE
# -------------------------
surcharge = 0
if taxable_income > 5000000:
    if taxable_income <= 10000000:
        surcharge = tax_after_rebate * 0.05
    elif taxable_income <= 20000000:
        surcharge = tax_after_rebate * 0.15
    else:
        surcharge = tax_after_rebate * 0.25

tax_plus_surcharge = tax_after_rebate + surcharge

# -------------------------
# CESS
# -------------------------
cess = tax_plus_surcharge * 0.04

total_tax = tax_plus_surcharge + cess

# -------------------------
# OUTPUT
# -------------------------
st.success(f"💵 Total Tax Payable: ₹{total_tax:,.0f}")

# -------------------------
# BREAKDOWN TABLE
# -------------------------
df = pd.DataFrame({
    "Component": [
        "Salary",
        "Standard Deduction",
        "Salary (Net)",
        "Gross Total Income",
        "Taxable Income",
        "Tax Before Rebate",
        "Rebate u/s 87A",
        "Tax After Rebate",
        "Surcharge",
        "Cess",
        "Total Tax"
    ],
    "Amount": [
        salary,
        std_deduction,
        salary_net,
        gross_total_income,
        taxable_income,
        tax_before_rebate,
        rebate,
        tax_after_rebate,
        surcharge,
        cess,
        total_tax
    ]
})

st.table(df)

# -------------------------
# GRAPH
# -------------------------
labels = ["Income", "Taxable Income", "Tax"]
values = [gross_total_income, taxable_income, total_tax]

fig, ax = plt.subplots()
ax.bar(labels, values, color=["#3498db", "#f39c12", "#2ecc71"])
st.pyplot(fig)

# -------------------------
# 🎨 EXTRA STYLING
# -------------------------
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to right, #eef2f3, #dfe9f3);
    }
    h1, h2, h3 {
        color: #1f4e79;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("## 📊 Detailed Tax Visualization")

# -------------------------
# SLAB-WISE BREAKDOWN FUNCTION
# -------------------------
def slab_breakdown(income):
    slabs = [
        ("0 - 4L", 400000, 0),
        ("4L - 8L", 800000, 0.05),
        ("8L - 12L", 1200000, 0.10),
        ("12L - 16L", 1600000, 0.15),
        ("16L - 20L", 2000000, 0.20),
        ("20L - 24L", 2400000, 0.25),
        ("Above 24L", float('inf'), 0.30)
    ]

    prev = 0
    data = []

    for label, limit, rate in slabs:
        if income > prev:
            taxable = min(income, limit) - prev
            tax_amt = taxable * rate
            data.append([label, taxable, rate * 100, tax_amt])
            prev = limit
        else:
            data.append([label, 0, rate * 100, 0])

    return pd.DataFrame(data, columns=["Slab", "Income in Slab", "Rate (%)", "Tax"])

slab_df = slab_breakdown(taxable_income)

# -------------------------
# TABLE
# -------------------------
st.markdown("### 📋 Slab-wise Tax Table")
st.dataframe(slab_df.style.background_gradient(cmap='Blues'))

# -------------------------
# ✅ HORIZONTAL BAR CHART (UPDATED)
# -------------------------
st.markdown("### 📊 Tax Contribution by Slab (Professional View)")

fig1, ax1 = plt.subplots(figsize=(10, 6))

bars = ax1.barh(
    slab_df["Slab"],
    slab_df["Tax"],
    color="#2E86C1",
    edgecolor="black"
)

# Value labels
for bar in bars:
    width = bar.get_width()
    ax1.text(
        width + (max(slab_df["Tax"]) * 0.01 if max(slab_df["Tax"]) > 0 else 1),
        bar.get_y() + bar.get_height() / 2,
        f"₹{int(width):,}",
        va='center',
        fontsize=9
    )

# Styling
ax1.set_xlabel("Tax Amount (₹)", fontsize=11)
ax1.set_ylabel("Tax Slabs", fontsize=11)
ax1.set_title("Slab-wise Tax Distribution", fontsize=13, fontweight='bold')

ax1.grid(axis='x', linestyle='--', alpha=0.6)
ax1.set_axisbelow(True)

for spine in ["top", "right"]:
    ax1.spines[spine].set_visible(False)

st.pyplot(fig1)

# -------------------------
# PIE CHART
# -------------------------
st.markdown("### 🥧 Tax Composition")

components = {
    "Tax": tax_after_rebate,
    "Surcharge": surcharge,
    "Cess": cess
}

fig2, ax2 = plt.subplots()
ax2.pie(
    components.values(),
    labels=components.keys(),
    autopct='%1.1f%%',
    colors=["#3498db", "#e67e22", "#2ecc71"]
)

ax2.set_title("Tax Composition Breakdown")
st.pyplot(fig2)

# -------------------------
# INCOME VS TAX
# -------------------------
st.markdown("### 📈 Income vs Tax Comparison")

fig3, ax3 = plt.subplots()
ax3.bar(
    ["Gross Income", "Taxable Income", "Final Tax"],
    [gross_total_income, taxable_income, total_tax],
    color=["#5dade2", "#f5b041", "#58d68d"]
)

for i, v in enumerate([gross_total_income, taxable_income, total_tax]):
    ax3.text(i, v, f"₹{int(v):,}", ha='center', va='bottom')

ax3.set_title("Income vs Tax Overview")
st.pyplot(fig3)

# -------------------------
# 📋 LEAD GENERATION FORM
# -------------------------
st.markdown("---")
st.markdown("## 📞 Get Expert Help / Save Your Tax Report")

st.markdown("""
Fill in your details to:
- 📩 Receive your tax summary
- 📊 Get expert consultation
- 💡 Personalized tax-saving tips
""")

with st.form("lead_form"):
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("👤 Full Name")
        email = st.text_input("📧 Email Address")

    with col2:
        phone = st.text_input("📱 Phone Number")
        city = st.text_input("🏙️ City")

    message = st.text_area("📝 Additional Notes (optional)")

    submitted = st.form_submit_button("🚀 Submit & Get Report")

# -------------------------
# FORM HANDLING
# -------------------------
if submitted:
    if name and email:
        st.success("✅ Thank you! Your details have been submitted successfully.")

        # Display summary (can be replaced with DB/Google Sheets later)
        lead_data = {
            "Name": name,
            "Email": email,
            "Phone": phone,
            "City": city,
            "Message": message,
            "Income": gross_total_income,
            "Taxable Income": taxable_income,
            "Tax Payable": total_tax
        }

        st.markdown("### 📄 Your Submitted Details")
        st.json(lead_data)

        st.info("📌 We will contact you shortly with your tax insights.")
    else:
        st.error("⚠️ Please fill at least Name and Email.")
